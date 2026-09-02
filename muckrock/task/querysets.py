"""
Custom QuerySets for the Task application
"""

# Django
from django.db import models
from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Cast, Coalesce, Now

# Standard Library
from datetime import date

# MuckRock
from muckrock import task
from muckrock.agency.models import AgencyEmail
from muckrock.communication.models import EmailCommunication, EmailError
from muckrock.core.models import ExtractDay
from muckrock.foia.models import FOIACommunication, FOIAComposer, FOIAFile, FOIARequest
from muckrock.foia.querysets import FOIACommunicationQuerySet, PreloadFileQuerysetMixin


class TaskQuerySet(models.QuerySet):
    """Object manager for all tasks"""

    def get_unresolved(self):
        """Get all unresolved tasks"""
        return self.filter(resolved=False)

    def get_resolved(self):
        """Get all resolved tasks"""
        return self.filter(resolved=True)

    def filter_by_foia(self, foia, user):
        """
        Get tasks that relate to the provided FOIA request.
        If user has permission to view tasks, get all tasks.
        For all users, get new agency task.
        """
        tasks = []
        # tasks that point to a communication
        communication_task_types = [
            task.models.ResponseTask,
            task.models.SnailMailTask,
            task.models.PortalTask,
        ]
        has_perm = foia.has_perm(user, "tasks")
        if has_perm:
            for task_type in communication_task_types:
                tasks += list(
                    task_type.objects.filter(communication__foia=foia).preload_list()
                )
        # tasks that point to a foia
        foia_task_types = [
            task.models.FlaggedTask,
            task.models.StatusChangeTask,
            task.models.PaymentInfoTask,
        ]
        if has_perm:
            for task_type in foia_task_types:
                tasks += list(task_type.objects.filter(foia=foia).preload_list())
        # tasks that point to a composer
        foia_task_types = [task.models.MultiRequestTask]
        if has_perm:
            for task_type in foia_task_types:
                tasks += list(
                    task_type.objects.filter(composer=foia.composer).preload_list()
                )
        # tasks that point to an agency
        if foia.agency:
            tasks += list(
                task.models.NewAgencyTask.objects.filter(
                    agency=foia.agency
                ).preload_list()
            )
        # review agency tasks are still staff only
        if foia.agency and user.is_staff:
            tasks += list(
                task.models.ReviewAgencyTask.objects.filter(
                    agency=foia.agency
                ).preload_list()
            )
        return tasks

    def get_undeferred(self):
        """Get tasks which aren't deferred"""
        return self.filter(Q(date_deferred__lte=date.today()) | Q(date_deferred=None))

    def get_deferred(self):
        """Get tasks which are deferred"""
        return self.filter(date_deferred__gt=date.today())


class CommunicationTaskMixin(PreloadFileQuerysetMixin):
    """Mixin for preloading tasks with a communication"""

    files_path = "communication__files"
    comm_id = "communication_id"

    def preload_communication(self):
        """Preload models on the communication"""
        return (
            self.select_related("communication")
            .prefetch_related(
                *[
                    "communication__{}".format(f)
                    for f in FOIACommunicationQuerySet.prefetch_fields
                ]
            )
            .preload_files()
        )

    def preload_files(self, limit=11):
        """Add communication select related"""
        queryset = super().preload_files(limit=limit)
        return queryset.select_related("communication")

    def _process_preloaded_files(self, obj, files):
        """What to do with the preloaded files for each record"""
        obj.communication.display_files = files.get(obj.communication.pk, [])

    def preload_communication_siblings(self):
        """Preload all communications on the communication's FOIA request"""
        return self.select_related("communication__foia").prefetch_related(
            Prefetch(
                "communication__foia__communications",
                queryset=FOIACommunication.objects.preload_list(),
            )
        )


class OrphanTaskQuerySet(TaskQuerySet):
    """Object manager for orphan tasks"""

    def get_from_domain(self, domain):
        """Get all orphan tasks from a specific domain"""
        return self.filter(communication__emails__from_email__email__icontains=domain)

    def preload_list(self):
        """Preloadrelations for list display"""
        return self.select_related(
            "communication__likely_foia__agency__jurisdiction", "resolved_by__profile"
        ).prefetch_related(
            "communication__files",
            Prefetch(
                "communication__emails",
                queryset=EmailCommunication.objects.exclude(rawemail=None),
                to_attr="raw_emails",
            ),
            Prefetch(
                "communication__emails",
                queryset=EmailCommunication.objects.select_related("from_email"),
            ),
        )


class SnailMailTaskQuerySet(CommunicationTaskMixin, TaskQuerySet):
    """Object manager for snail mail tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        # pylint: disable=import-outside-toplevel
        # MuckRock
        from muckrock.agency.models import AgencyAddress, AgencyEmail, AgencyPhone

        return (
            self.select_related(
                "communication__foia__agency__portal",
                "communication__foia__agency__appeal_agency__portal",
                "communication__foia__agency__jurisdiction__law",
                "communication__foia__agency__jurisdiction__parent__law",
                "communication__foia__composer__user",
                "communication__foia__address",
                "resolved_by__profile",
            )
            .prefetch_related(
                "communication__foia__tracking_ids",
                "communication__files",
                Prefetch(
                    "communication__foia__communications",
                    queryset=FOIACommunication.objects.filter(response=True),
                    to_attr="ack",
                ),
                Prefetch(
                    "communication__foia__agency__agencyemail_set",
                    queryset=AgencyEmail.objects.select_related("email"),
                ),
                Prefetch(
                    "communication__foia__agency__agencyphone_set",
                    queryset=AgencyPhone.objects.select_related("phone"),
                ),
                Prefetch(
                    "communication__foia__agency__agencyaddress_set",
                    queryset=AgencyAddress.objects.select_related("address"),
                ),
                Prefetch(
                    "communication__foia__agency__appeal_agency__agencyemail_set",
                    queryset=AgencyEmail.objects.select_related("email"),
                ),
                Prefetch(
                    "communication__foia__agency__appeal_agency__agencyphone_set",
                    queryset=AgencyPhone.objects.select_related("phone"),
                ),
                Prefetch(
                    "communication__foia__agency__appeal_agency__agencyaddress_set",
                    queryset=AgencyAddress.objects.select_related("address"),
                ),
            )
            .preload_communication()
            .preload_communication_siblings()
        )

    def preload_pdf(self):
        """Preload relations for PDF generation"""
        return (
            self.select_related(
                "communication__foia__address",
                "communication__foia__agency",
                "communication__foia__composer__user",
                "communication__from_user",
            )
            .preload_communication()
            .preload_communication_siblings()
        )


class FlaggedTaskQuerySet(TaskQuerySet):
    """Object manager for flagged tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return self.select_related(
            "agency",
            "foia__agency__jurisdiction",
            "jurisdiction",
            "user",
            "resolved_by__profile",
        )

    def get_processing_days(self):
        """Get total processing days for flagged tasks"""
        return (
            self.exclude(resolved=True)
            .get_undeferred()
            .aggregate(
                days=ExtractDay(
                    Cast(Sum(Now() - F("date_created")), models.DurationField())
                )
            )["days"]
        )


class ProjectReviewTaskQuerySet(TaskQuerySet):
    """Object manager for project review tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return self.select_related("project", "resolved_by__profile").prefetch_related(
            Prefetch(
                "project__requests",
                queryset=FOIARequest.objects.select_related("agency__jurisdiction"),
            ),
            "project__articles",
            "project__contributors",
        )


class NewAgencyTaskQuerySet(TaskQuerySet):
    """Object manager for new agency tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        # pylint: disable=import-outside-toplevel
        # MuckRock
        from muckrock.agency.models import AgencyAddress, AgencyEmail, AgencyPhone

        return self.select_related(
            "agency__jurisdiction__parent",
            "agency__user",
            "agency__portal",
            "user",
            "resolved_by__profile",
        ).prefetch_related(
            Prefetch(
                "agency__agencyemail_set",
                queryset=AgencyEmail.objects.select_related("email"),
            ),
            Prefetch(
                "agency__agencyphone_set",
                queryset=AgencyPhone.objects.select_related("phone"),
            ),
            Prefetch(
                "agency__agencyaddress_set",
                queryset=AgencyAddress.objects.select_related("address"),
            ),
            Prefetch(
                "agency__foiarequest_set",
                queryset=FOIARequest.objects.select_related(
                    "agency__jurisdiction", "composer"
                ),
            ),
            Prefetch(
                "agency__composers",
                queryset=FOIAComposer.objects.filter(status="started"),
                to_attr="pending_drafts",
            ),
        )


class ReviewAgencyTaskQuerySet(TaskQuerySet):
    """Object manager for review agency tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        # pylint: disable=import-outside-toplevel
        # MuckRock
        from muckrock.agency.models import AgencyAddress, AgencyEmail, AgencyPhone

        return (
            self.annotate_channel()
            .select_related(
                "agency__jurisdiction",
                "agency__portal",
                "resolved_by__profile",
                "email",
            )
            .prefetch_related(
                "tags",
                Prefetch(
                    "agency__agencyemail_set",
                    queryset=AgencyEmail.objects.select_related("email"),
                ),
                Prefetch(
                    "agency__agencyphone_set",
                    queryset=AgencyPhone.objects.select_related("phone"),
                ),
                Prefetch(
                    "agency__agencyaddress_set",
                    queryset=AgencyAddress.objects.select_related("address"),
                ),
            )
        )

    def annotate_blocked(self):
        """Annotate each task with the number of live requests it is blocking

        This is the queue's ordering key.  A channel scoped task counts the
        open requests routed at its channel; an agency level task (staff or
        stale, with no channel) counts all of the agency's open requests,
        because that task really is about the agency.
        """
        open_requests = FOIARequest.objects.get_open()

        channel_blocked = Subquery(
            open_requests.filter(agency=OuterRef("agency"), email=OuterRef("email"))
            .values("agency")
            .annotate(count=Count("pk"))
            .values("count"),
            output_field=IntegerField(),
        )
        agency_blocked = Subquery(
            open_requests.filter(agency=OuterRef("agency"))
            .values("agency")
            .annotate(count=Count("pk"))
            .values("count"),
            output_field=IntegerField(),
        )
        return self.annotate(
            blocked_count=Coalesce(
                Case(
                    When(email__isnull=True, then=agency_blocked),
                    default=channel_blocked,
                    output_field=IntegerField(),
                ),
                Value(0),
                output_field=IntegerField(),
            ),
            # The agency's whole load, so its channels can be kept together in
            # the queue while agencies still compete on impact.
            agency_blocked_count=Coalesce(
                agency_blocked, Value(0), output_field=IntegerField()
            ),
        )

    def annotate_channel(self):
        """Annotate the summary the queue row needs to be legible

        Which channel is broken, whether it is the agency's primary contact,
        how it last failed and how long ago, and when it last delivered.  All
        as subqueries so the queue's cost does not grow with its length.
        """
        newest_error = EmailError.objects.filter(recipient=OuterRef("email")).order_by(
            "-datetime"
        )

        return self.annotate(
            channel_last_error=Subquery(newest_error.values("datetime")[:1]),
            channel_last_error_code=Subquery(newest_error.values("code")[:1]),
            channel_last_error_reason=Subquery(newest_error.values("reason")[:1]),
            channel_error_count=Coalesce(
                Subquery(
                    EmailError.objects.filter(recipient=OuterRef("email"))
                    .values("recipient")
                    .annotate(count=Count("pk"))
                    .values("count"),
                    output_field=IntegerField(),
                ),
                Value(0),
                output_field=IntegerField(),
            ),
            channel_last_confirm=Subquery(
                EmailCommunication.objects.filter(
                    to_emails=OuterRef("email"), confirmed_datetime__isnull=False
                )
                .order_by("-confirmed_datetime")
                .values("confirmed_datetime")[:1]
            ),
            channel_is_primary=Exists(
                AgencyEmail.objects.filter(
                    agency=OuterRef("agency"),
                    email=OuterRef("email"),
                    request_type="primary",
                    email_type="to",
                )
            ),
        )

    def ensure_one_created(self, source=None, **kwargs):
        """Ensure exactly one model exists in the database as specified"""
        try:
            task_, _ = self.get_or_create(**kwargs, defaults={"source": source})
            return task_
        except task.models.ReviewAgencyTask.MultipleObjectsReturned:
            # if there are multiples, delete all but the first one
            # then try again
            to_delete = self.filter(**kwargs).order_by("date_created")[1:]
            self.filter(pk__in=to_delete).delete()
            return self.ensure_one_created(source=source, **kwargs)


class ResponseTaskQuerySet(CommunicationTaskMixin, TaskQuerySet):
    """Object manager for response tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return (
            self.select_related(
                "communication__foia__agency__jurisdiction",
                "communication__from_user__profile__agency",
                "resolved_by__profile",
            )
            .prefetch_related(
                Prefetch(
                    "communication__files",
                    queryset=FOIAFile.objects.select_related(
                        "comm__foia__agency__jurisdiction"
                    ),
                ),
                Prefetch(
                    "communication__foia__communications",
                    queryset=FOIACommunication.objects.order_by("-datetime")
                    .select_related("from_user__profile__agency")
                    .preload_list(),
                    to_attr="reverse_communications",
                ),
                Prefetch(
                    "communication__emails",
                    queryset=EmailCommunication.objects.select_related("from_email"),
                ),
                "communication__foia__tracking_ids",
            )
            .preload_communication()
        )


class StatusChangeTaskQuerySet(TaskQuerySet):
    """Object manager for status change tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return self.select_related(
            "foia__agency__jurisdiction", "user", "resolved_by__profile"
        )


class CrowdfundTaskQuerySet(TaskQuerySet):
    """Object manager for crowdfund tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return self.select_related(
            "crowdfund__foia__agency__jurisdiction", "resolved_by__profile"
        )


class MultiRequestTaskQuerySet(TaskQuerySet):
    """Object manager for multirequest tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return self.select_related(
            "composer__user", "resolved_by__profile"
        ).prefetch_related("composer__agencies")


class PortalTaskQuerySet(CommunicationTaskMixin, TaskQuerySet):
    """Object manager for portal tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return (
            self.select_related(
                "communication__foia__agency__jurisdiction",
                "communication__foia__composer__user",
                "communication__foia__portal",
                "communication__from_user__profile__agency",
                "resolved_by__profile",
            )
            .prefetch_related(
                Prefetch(
                    "communication__foia__communications",
                    queryset=FOIACommunication.objects.filter(response=True),
                    to_attr="ack",
                ),
                Prefetch(
                    "communication__foia__communications",
                    queryset=FOIACommunication.objects.order_by("-datetime")
                    .select_related("from_user__profile__agency")
                    .preload_list(),
                    to_attr="reverse_communications",
                ),
                "communication__files",
                "communication__foia__tracking_ids",
            )
            .preload_communication()
        )


class NewPortalTaskQuerySet(CommunicationTaskMixin, TaskQuerySet):
    """Object manager for new portal tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return self.select_related(
            "communication__foia__agency__jurisdiction",
            "communication__foia__composer__user",
            "communication__from_user__profile__agency",
            "resolved_by__profile",
        ).preload_communication()


class PaymentInfoTaskQuerySet(TaskQuerySet):
    """Object manager for payment info tasks"""

    def preload_list(self):
        """Preload relations for list display"""
        return self.select_related(
            "foia__agency__jurisdiction", "resolved_by__profile"
        ).prefetch_related(
            Prefetch(
                "foia__communications",
                queryset=FOIACommunication.objects.order_by("-datetime")
                .select_related("from_user__profile__agency")
                .preload_list(),
                to_attr="reverse_communications",
            )
        )
