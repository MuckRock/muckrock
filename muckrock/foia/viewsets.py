"""
Viewsets for the FOIA API
"""

# Django
from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Prefetch
from django.template.defaultfilters import slugify
from django.utils import timezone

# Standard Library
import logging

# Third Party
import actstream
import django_filters
import requests
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, status as http_status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response

# MuckRock
from muckrock.agency.models import Agency
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.foia.models import FOIACommunication, FOIAComposer, FOIARequest
from muckrock.foia.serializers import (
    FOIACommunicationSerializer,
    FOIAPermissions,
    FOIARequestSerializer,
    IsOwner,
)
from muckrock.task.models import ResponseTask

logger = logging.getLogger(__name__)


class FOIARequestViewSet(viewsets.ModelViewSet):
    """
    API views for FOIARequest

    Filter fields:
    * title
    * embargo
    * user, by username
    * jurisdiction, by id
    * agency, by id
    * tags, by name
    """

    # pylint: disable=too-many-public-methods
    serializer_class = FOIARequestSerializer
    permission_classes = (FOIAPermissions,)
    # remove default ordering backend as it does not work well with fields stored
    # on related models
    filter_backends = (DjangoFilterBackend, SearchFilter)

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Requests"""

        agency = django_filters.NumberFilter(field_name="agency__id")
        jurisdiction = django_filters.NumberFilter(
            field_name="agency__jurisdiction__id", label="Jurisdiction ID"
        )
        projects = django_filters.NumberFilter(
            field_name="projects", label="Project ID"
        )
        user = django_filters.CharFilter(
            field_name="composer__user__username", label="User"
        )
        tags = django_filters.CharFilter(field_name="tags__name", label="Tags")
        has_datetime_submitted = django_filters.BooleanFilter(
            field_name="composer__datetime_submitted",
            label="Has DateTime Submitted",
            lookup_expr="isnull",
            exclude=True,
        )
        has_datetime_done = django_filters.BooleanFilter(
            field_name="datetime_done",
            label="Has DateTime Done",
            lookup_expr="isnull",
            exclude=True,
        )

        order_by_field = "ordering"
        ordering = django_filters.OrderingFilter(
            fields=(
                ("composer__datetime_submitted", "datetime_submitted"),
                ("composer__user__username", "user"),
                ("agency__name", "agency"),
                ("datetime_done", "datetime_done"),
                ("title", "title"),
                ("status", "status"),
            )
        )

        class Meta:
            model = FOIARequest
            fields = ("user", "title", "status", "embargo", "jurisdiction", "agency")

    filterset_class = Filter

    def get_queryset(self):
        return (
            FOIARequest.objects.get_viewable(self.request.user)
            .select_related("composer__user", "agency__jurisdiction")
            .prefetch_related(
                "communications__files",
                "communications__emails",
                "communications__faxes",
                "communications__mails",
                "communications__web_comms",
                "communications__portals",
                "notes",
                "tags",
                "edit_collaborators",
                "read_collaborators",
                "tracking_ids",
                Prefetch(
                    "communications__responsetask_set",
                    queryset=ResponseTask.objects.select_related("resolved_by"),
                ),
            )
        )

    def _validate_create(self, user, data):
        """Do all of the data validation for request creation"""
        cleaned_data = {}
        cleaned_data["agencies"] = self._clean_agencies(data.get("agency", []))
        (
            cleaned_data["embargo"],
            cleaned_data["permanent_embargo"],
        ) = self._clean_embargo(
            user, data.get("embargo", False), data.get("permanent_embargo", False)
        )
        cleaned_data["title"] = self._clean_title(data.get("title"))

        (
            cleaned_data["requested_docs"],
            cleaned_data["edited_boilerplate"],
        ) = self._clean_document_request(
            data.get("document_request"), data.get("full_text")
        )

        cleaned_data["attachments"] = self._clean_attachments(
            data.get("attachments", [])
        )
        return cleaned_data

    def _clean_agencies(self, agencies):
        """Clean agencies"""
        if not isinstance(agencies, list):
            agencies = [agencies]
        try:
            agencies = Agency.objects.filter(pk__in=agencies, status="approved")
        except ValueError:
            raise forms.ValidationError("Bad agency ID format")

        if not agencies:
            raise forms.ValidationError("At least one valid agency required")
        return agencies

    def _clean_embargo(self, user, embargo, permanent_embargo):
        """Clean embargo and permanent embargo"""
        if permanent_embargo:
            embargo = True
        if embargo and not user.has_perm("foia.embargo_foiarequest"):
            raise forms.ValidationError(
                "You do not have permission to embargo requests"
            )
        if permanent_embargo and not user.has_perm("foia.embargo_perm_foiarequest"):
            raise forms.ValidationError(
                "You do not have permission to permanently embargo requests"
            )
        return embargo, permanent_embargo

    def _clean_title(self, title):
        """Clean title"""
        if not title:
            raise forms.ValidationError("title required")
        return title

    def _clean_document_request(self, document_request, full_text):
        """Clean document_request"""
        if full_text:
            return full_text, True
        elif document_request:
            return document_request, False
        else:
            raise forms.ValidationError("document_request or full_text required")

    def _clean_attachments(self, attachments):
        """Clean attachments"""

        clean_attachments = []

        if not isinstance(attachments, list):
            raise forms.ValidationError(
                "attachments should be a list of publicly available URLs"
            )

        total_size = 0
        for attm_path in attachments[:3]:
            try:
                res = requests.get(attm_path)
            except requests.exceptions.RequestException:
                raise forms.ValidationError(
                    "Error downloading attachment: {}".format(attm_path)
                )
            mime_type = res.headers.get("Content-Type")
            if mime_type not in settings.ALLOWED_FILE_MIMES:
                raise forms.ValidationError(
                    "Attachment: {} is not of a valid mime type.  Valid types "
                    "include: {}".format(
                        attm_path, ", ".join(settings.ALLOWED_FILE_MIMES)
                    )
                )
            if res.status_code != 200:
                raise forms.ValidationError(
                    "Error downloading attachment: {}, code: {}".format(
                        attm_path, res.status_code
                    )
                )
            len_res = len(res.content)
            if len_res > settings.MAX_ATTACHMENT_SIZE:
                raise forms.ValidationError(
                    "Attachment too large (5MB): {}".format(attm_path)
                )
            total_size += len_res
            if total_size > settings.MAX_ATTACHMENT_TOTAL_SIZE:
                raise forms.ValidationError(
                    "Total attachment size must be less than 20MB"
                )
            title = attm_path.rsplit("/", 1)[1]
            clean_attachments.append((title, res.content))
        return clean_attachments

    def create(self, request, *_args, **_kwargs):
        """Submit new request"""
        try:
            data = self._validate_create(request.user, request.data)
        except forms.ValidationError as exc:
            return Response(
                {"status": exc.args[0]}, status=http_status.HTTP_400_BAD_REQUEST
            )

        composer = FOIAComposer.objects.create(
            user=request.user,
            organization=request.user.profile.organization,
            title=data["title"],
            slug=slugify(data["title"]) or "untitled",
            requested_docs=data["requested_docs"],
            edited_boilerplate=data["edited_boilerplate"],
            embargo=data["embargo"],
            permanent_embargo=data["permanent_embargo"],
        )
        composer.agencies.set(data["agencies"])

        for title, content in data["attachments"]:
            attm = composer.pending_attachments.create(
                user=request.user, date_time_stamp=timezone.now()
            )
            attm.ffile.save(title, ContentFile(content))

        try:
            composer.submit()
        except InsufficientRequestsError:
            return Response(
                {
                    "status": "Out of requests.  FOI Request has been saved.",
                    "Location": composer.get_absolute_url(),
                },
                status=http_status.HTTP_402_PAYMENT_REQUIRED,
            )
        else:
            return Response(
                {
                    "status": "FOI Request submitted",
                    "Location": composer.get_absolute_url(),
                    "Requests": [f.pk for f in composer.foias.all()],
                },
                status=http_status.HTTP_201_CREATED,
            )

    @decorators.action(detail=True, permission_classes=(IsOwner,))
    def followup(self, request, pk=None):
        """Followup on a request"""
        try:
            foia = FOIARequest.objects.get(pk=pk)
            self.check_object_permissions(request, foia)

            foia.create_out_communication(
                from_user=request.user, text=request.DATA["text"]
            )

            can_appeal = request.user.has_perm("foia.appeal_foiarequest", foia)
            appeal = request.DATA.get("appeal", False) and can_appeal
            foia.submit(appeal=appeal)

            if appeal:
                status = "Appeal submitted"
            else:
                status = "Follow up submitted"

            return Response({"status": status}, status=http_status.HTTP_200_OK)

        except FOIARequest.DoesNotExist:
            return Response(
                {"status": "Not Found"}, status=http_status.HTTP_404_NOT_FOUND
            )

        except KeyError:
            return Response(
                {"status": "Missing data - Please supply text for followup"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

    @decorators.action(
        detail=True, methods=["POST", "DELETE"], permission_classes=(IsAuthenticated,)
    )
    def follow(self, request, pk=None):
        """Follow or unfollow a request"""

        try:
            foia = FOIARequest.objects.get(pk=pk)
            self.check_object_permissions(request, foia)

            if foia.user == request.user:
                return Response(
                    {"status": "You may not follow your own request"},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )

            if request.method == "POST":
                actstream.actions.follow(request.user, foia, actor_only=False)
                return Response({"status": "Following"}, status=http_status.HTTP_200_OK)
            elif request.method == "DELETE":
                actstream.actions.unfollow(request.user, foia)
                return Response(
                    {"status": "Not following"}, status=http_status.HTTP_200_OK
                )
            else:
                return Response(status=http_status.HTTP_400_BAD_REQUEST)

        except FOIARequest.DoesNotExist:
            return Response(
                {"status": "Not Found"}, status=http_status.HTTP_404_NOT_FOUND
            )

    def post_save(self, obj, created=False):
        """Save tags"""
        if "tags" in self.request.DATA:
            obj.tags.set(*self.request.DATA["tags"])
        return super(FOIARequestViewSet, self).post_save(obj, created=created)


DELIVERED_CHOICES = (
    ("email", "Email"),
    ("fax", "Fax"),
    ("mail", "Mail"),
    ("web", "Web Comm"),
    ("portal", "Portal"),
)


class FOIACommunicationViewSet(viewsets.ModelViewSet):
    """API views for FOIACommunication"""

    # pylint: disable=too-many-public-methods
    serializer_class = FOIACommunicationSerializer
    permission_classes = (DjangoModelPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Communications"""

        min_date = django_filters.DateFilter(field_name="datetime", lookup_expr="gte")
        max_date = django_filters.DateFilter(field_name="datetime", lookup_expr="lte")
        foia = django_filters.NumberFilter(field_name="foia__id")
        delivered = django_filters.ChoiceFilter(
            method="filter_delivered", choices=DELIVERED_CHOICES
        )

        def filter_delivered(self, queryset, name, value):
            """Filter by delivered"""
            # pylint: disable=unused-argument
            dmap = {
                "email": "emails",
                "fax": "faxes",
                "mail": "mails",
                "web": "web_comms",
                "portal": "portals",
            }
            if value not in dmap:
                return queryset
            return queryset.exclude(**{dmap[value]: None})

        class Meta:
            model = FOIACommunication
            fields = ("max_date", "min_date", "foia", "status", "response", "delivered")

    filterset_class = Filter

    def get_queryset(self):
        return FOIACommunication.objects.prefetch_related(
            "files",
            "emails",
            "faxes",
            "mails",
            "web_comms",
            "portals",
            Prefetch(
                "responsetask_set",
                queryset=ResponseTask.objects.select_related("resolved_by"),
            ),
        ).get_viewable(self.request.user)
