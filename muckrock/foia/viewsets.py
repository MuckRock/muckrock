"""
Viewsets for the FOIA API
"""

# Django
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Prefetch
from django.template.defaultfilters import slugify
from django.template.loader import get_template

# Standard Library
import logging
from datetime import datetime

# Third Party
import actstream
import django_filters
import requests
from rest_framework import status as http_status
from rest_framework import decorators, viewsets
from rest_framework.permissions import DjangoModelPermissions, IsAuthenticated
from rest_framework.response import Response

# MuckRock
from muckrock.agency.models import Agency
from muckrock.foia.exceptions import MimeError
from muckrock.foia.models import FOIACommunication, FOIAFile, FOIARequest
from muckrock.foia.serializers import (
    FOIACommunicationSerializer,
    FOIAPermissions,
    FOIARequestSerializer,
    IsOwner,
)
from muckrock.jurisdiction.models import Jurisdiction
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

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Requests"""
        agency = django_filters.NumberFilter(name='agency__id')
        jurisdiction = django_filters.NumberFilter(name='jurisdiction__id')
        user = django_filters.CharFilter(name='user__username')
        tags = django_filters.CharFilter(name='tags__name')

        class Meta:
            model = FOIARequest
            fields = (
                'user',
                'title',
                'status',
                'embargo',
                'jurisdiction',
                'agency',
            )

    filter_class = Filter

    def get_queryset(self):
        return (
            FOIARequest.objects.get_viewable(self.request.user)
            .select_related('user', 'agency', 'jurisdiction').prefetch_related(
                'communications__files',
                'communications__emails',
                'communications__faxes',
                'communications__mails',
                'communications__web_comms',
                'communications__portals',
                'notes',
                'tags',
                'edit_collaborators',
                'read_collaborators',
                'tracking_ids',
                Prefetch(
                    'communications__responsetask_set',
                    queryset=ResponseTask.objects.select_related('resolved_by'),
                ),
            )
        )

    def create(self, request):
        """Submit new request"""
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        data = request.data
        try:
            jurisdiction = Jurisdiction.objects.get(
                pk=int(data['jurisdiction'])
            )
            agency = Agency.objects.get(
                pk=int(data['agency']),
                jurisdiction=jurisdiction,
                status='approved',
            )

            embargo = data.get('embargo', False)
            permanent_embargo = data.get('permanent_embargo', False)
            if permanent_embargo:
                embargo = True

            if 'full_text' in data:
                text = data['full_text']
                requested_docs = data.get('document_request', '')
            else:
                requested_docs = data['document_request']
                template = get_template('text/foia/request.txt')
                context = {
                    'document_request': requested_docs,
                    'jurisdiction': jurisdiction,
                    'user_name': request.user.get_full_name,
                }
                text = template.render(context)

            title = data['title']

            slug = slugify(title) or 'untitled'
            foia = FOIARequest(
                user=request.user,
                status='started',
                title=title,
                jurisdiction=jurisdiction,
                slug=slug,
                agency=agency,
                requested_docs=requested_docs,
                description=requested_docs,
                embargo=embargo,
                permanent_embargo=permanent_embargo,
            )
            if embargo and not foia.has_perm(request.user, 'embargo'):
                return Response(
                    {
                        'status':
                            'You do not have permission to embargo requests.'
                    },
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            if permanent_embargo and not foia.has_perm(
                request.user, 'embargo_perm'
            ):
                return Response(
                    {
                        'status':
                            'You do not have permission to permanently '
                            'embargo requests.'
                    },
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            foia.save()

            comm = FOIACommunication.objects.create(
                foia=foia,
                communication=text,
                from_user=request.user,
                to_user=foia.get_to_user(),
                date=datetime.now(),
                response=False,
            )

            if 'attachments' in data:
                attachments = data.get('attachments')[:3]
            else:
                attachments = []
            for attm_path in attachments:
                res = requests.get(attm_path)
                mime_type = res.headers['Content-Type']
                if mime_type not in settings.ALLOWED_FILE_MIMES:
                    raise MimeError
                res.raise_for_status()
                title = attm_path.rsplit('/', 1)[1]
                file_ = FOIAFile.objects.create(
                    access='public',
                    comm=comm,
                    title=title,
                    date=datetime.now(),
                    source=request.user.get_full_name(),
                )
                file_.ffile.save(title, ContentFile(res.content))

            if request.user.profile.make_request():
                foia.submit()
                return Response(
                    {
                        'status': 'FOI Request submitted',
                        'Location': foia.get_absolute_url()
                    },
                    status=http_status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {
                        'status':
                            'Error - Out of requests.  FOI Request has been saved.',
                        'Location':
                            foia.get_absolute_url()
                    },
                    status=http_status.HTTP_402_PAYMENT_REQUIRED,
                )

        except KeyError:
            return Response(
                {
                    'status':
                        'Missing data - Please supply title, document_request, '
                        'jurisdiction, and agency'
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        except (Jurisdiction.DoesNotExist, Agency.DoesNotExist):
            return Response(
                {
                    'status':
                        'Bad data - please supply jurisdiction and agency as the PK'
                        ' of existing entities.  Agency must be in Jurisdiction.'
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        except (requests.exceptions.RequestException, TypeError, MimeError):
            # TypeError is thrown if 'attachments' is not a list
            return Response(
                {
                    'status': 'There was a problem with one of your attachments'
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

    @decorators.detail_route(permission_classes=(IsOwner,))
    def followup(self, request, pk=None):
        """Followup on a request"""
        try:
            foia = FOIARequest.objects.get(pk=pk)
            self.check_object_permissions(request, foia)

            foia.create_out_communication(
                from_user=request.user,
                text=request.DATA['text'],
            )

            can_appeal = request.user.has_perm('foia.appeal_foiarequest', foia)
            appeal = request.DATA.get('appeal', False) and can_appeal
            foia.submit(appeal=appeal)

            if appeal:
                status = 'Appeal submitted'
            else:
                status = 'Follow up submitted'

            return Response({'status': status}, status=http_status.HTTP_200_OK)

        except FOIARequest.DoesNotExist:
            return Response({
                'status': 'Not Found'
            },
                            status=http_status.HTTP_404_NOT_FOUND)

        except KeyError:
            return Response({
                'status': 'Missing data - Please supply text for followup'
            },
                            status=http_status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(
        methods=['POST', 'DELETE'], permission_classes=(IsAuthenticated,)
    )
    def follow(self, request, pk=None):
        """Follow or unfollow a request"""

        try:
            foia = FOIARequest.objects.get(pk=pk)
            self.check_object_permissions(request, foia)

            if foia.user == request.user:
                return Response({
                    'status': 'You may not follow your own request'
                },
                                status=http_status.HTTP_400_BAD_REQUEST)

            if request.method == 'POST':
                actstream.actions.follow(request.user, foia, actor_only=False)
                return Response({
                    'status': 'Following'
                },
                                status=http_status.HTTP_200_OK)
            if request.method == 'DELETE':
                actstream.actions.unfollow(request.user, foia)
                return Response({
                    'status': 'Not following'
                },
                                status=http_status.HTTP_200_OK)

        except FOIARequest.DoesNotExist:
            return Response({
                'status': 'Not Found'
            },
                            status=http_status.HTTP_404_NOT_FOUND)

    def post_save(self, obj, created=False):
        """Save tags"""
        if 'tags' in self.request.DATA:
            obj.tags.set(*self.request.DATA['tags'])
        return super(FOIARequestViewSet, self).post_save(obj, created=created)


DELIVERED_CHOICES = (
    ('email', 'Email'),
    ('fax', 'Fax'),
    ('mail', 'Mail'),
    ('web', 'Web Comm'),
    ('portal', 'Portal'),
)


class FOIACommunicationViewSet(viewsets.ModelViewSet):
    """API views for FOIARequest"""
    # pylint: disable=too-many-public-methods
    queryset = FOIACommunication.objects.prefetch_related(
        'files',
        'emails',
        'faxes',
        'mails',
        'web_comms',
        'portals',
        Prefetch(
            'responsetask_set',
            queryset=ResponseTask.objects.select_related('resolved_by'),
        ),
    )
    serializer_class = FOIACommunicationSerializer
    permission_classes = (DjangoModelPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Communications"""
        min_date = django_filters.DateFilter(name='date', lookup_expr='gte')
        max_date = django_filters.DateFilter(name='date', lookup_expr='lte')
        foia = django_filters.NumberFilter(name='foia__id')
        delivered = django_filters.ChoiceFilter(
            method='filter_delivered',
            choices=DELIVERED_CHOICES,
        )

        def filter_delivered(self, queryset, name, value):
            """Filter by delivered"""
            # pylint: disable=unused-argument
            dmap = {
                'email': 'emails',
                'fax': 'faxes',
                'mail': 'mails',
                'web': 'web_comms',
                'portal': 'portals',
            }
            if value not in dmap:
                return queryset
            return queryset.exclude(**{dmap[value]: None})

        class Meta:
            model = FOIACommunication
            fields = (
                'max_date',
                'min_date',
                'foia',
                'status',
                'response',
                'delivered',
            )

    filter_class = Filter
