"""
Custom QuerySets for the Task application
"""

# Django
from django.db import models
from django.db.models import F, Prefetch, Q, Sum
from django.db.models.functions import Cast, Now

# Standard Library
from datetime import date

# MuckRock
from muckrock import task
from muckrock.communication.models import EmailCommunication
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
            task.models.PaymentInfoTask,
            task.models.PortalTask,
        ]
        has_perm = foia.has_perm(user, "tasks")
        if has_perm:
            for task_type in communication_task_types:
                tasks += list(
                    task_type.objects.filter(communication__foia=foia).preload_list()
                )
        # tasks that point to a foia
        foia_task_types = [task.models.FlaggedTask, task.models.StatusChangeTask]
        if has_perm:
            for task_type in foia_task_types:
                tasks += list(task_type.objects.filter(foia=foia).preload_list())
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
        queryset = super(CommunicationTaskMixin, self).preload_files(limit=limit)
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
        from muckrock.agency.models import AgencyEmail, AgencyPhone, AgencyAddress

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
        from muckrock.agency.models import AgencyEmail, AgencyPhone, AgencyAddress

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
        from muckrock.agency.models import AgencyEmail, AgencyPhone, AgencyAddress

        return self.select_related(
            "agency__jurisdiction", "agency__portal", "resolved_by__profile"
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
        )

    def ensure_one_created(self, **kwargs):
        """Ensure exactly one model exists in the database as specified"""
        try:
            task_, _ = self.get_or_create(**kwargs)
            return task_
        except task.models.ReviewAgencyTask.MultipleObjectsReturned:
            # if there are multiples, delete all but the first one
            # then try again
            to_delete = self.filter(**kwargs).order_by("date_created")[1:]
            self.filter(pk__in=to_delete).delete()
            self.ensure_one_created(**kwargs)


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
            "communication__foia__agency__jurisdiction", "resolved_by__profile"
        ).prefetch_related(
            Prefetch(
                "communication__foia__communications",
                queryset=FOIACommunication.objects.order_by("-datetime")
                .select_related("from_user__profile__agency")
                .preload_list(),
                to_attr="reverse_communications",
            )
        )
