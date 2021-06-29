"""
Digest objects for the messages app
"""

# Django
from django.contrib.auth.models import User
from django.db.models import DurationField, F, Q
from django.db.models.functions import Cast, Now
from django.utils import timezone

# Standard Library
from collections import OrderedDict
from datetime import date, timedelta

# Third Party
from actstream.models import Action
from dateutil.relativedelta import relativedelta

# MuckRock
from muckrock.accounts.models import Notification, Statistics
from muckrock.communication.models import (
    Check,
    EmailCommunication,
    FaxCommunication,
    MailCommunication,
)
from muckrock.core.models import ExtractDay
from muckrock.crowdfund.models import Crowdfund
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.message.email import TemplateEmail
from muckrock.qanda.models import Question


def get_salutation():
    """Returns a time-appropriate salutation"""
    hour = timezone.now().hour
    if hour < 12:
        salutation = "Good morning"
    elif hour < 18:
        salutation = "Good afternoon"
    else:
        salutation = "Good evening"
    return salutation


def get_signoff():
    """Returns a time-appropriate signoff"""
    hour = timezone.now().hour
    if hour < 18:
        signoff = "Have a great day"
    else:
        signoff = "Have a great night"
    return signoff


class Digest(TemplateEmail):
    """A digest is sent at a regular scheduled interval."""

    interval = None

    def __init__(self, interval=None, **kwargs):
        """Saves interval attribute if provided."""
        if interval:
            # we use relativedelta in addition to timedelta because it gives us a greater
            # flexibility in the kinds of intervals we can define, e.g. weeks and months
            if isinstance(interval, (relativedelta, timedelta)):
                self.interval = interval
            else:
                raise TypeError("Interval must be relativedelta or timedelta")
        super(Digest, self).__init__(**kwargs)

    def get_context_data(self, *args):
        """Adds time-based salutation and signature context"""
        context = super(Digest, self).get_context_data(*args)
        context["salutation"] = get_salutation()
        context["signoff"] = get_signoff()
        context["last"] = self.get_duration()
        return context

    def get_duration(self):
        """Returns the start of the duration for the digest."""
        return timezone.now() - self.get_interval()

    def get_interval(self):
        """Gets the interval or raises an error if it is missing or an unexpected type."""
        if not self.interval:
            raise NotImplementedError(
                "Interval must be provided by subclass or when initialized."
            )
        return self.interval

    def get_user(self):
        """Gets the user or raises an error if it is missing."""
        if not self.user:
            raise NotImplementedError("User must be provided to a digest.")
        return self.user


class ActivityDigest(Digest):
    """
    An ActivityDigest describes a collection of activity over a duration, which
    is then rendered into an email and delivered at a scheduled interval.
    """

    text_template = "message/digest/digest.txt"
    html_template = "message/digest/digest.html"

    # Here we scaffold out the activity dictionary.
    # It is scaffolded to prevent key errors when counting
    # activity, as well as to provide some guidance for
    # which activities to filter from the global stream.

    # Activity is independent from template context because
    # we use activity counts to influence other parts of the
    # email, like the subject line and whether or not to
    # even send the email at all.

    activity = {
        "count": 0,
        "requests": {"count": 0, "mine": None, "following": None},
        "questions": {"count": 0, "mine": None, "following": None},
    }

    # Most of the work re: composing the email takes place
    # at init. This is by design, since digests should require
    # a minimum of configuration outside of their own configuration,
    # which is their responsibility. In other words, a digest really
    # only needs to know its user.

    # Question: should interval be made into a required init value?
    # On the one hand, having interval hardcoded into subclasses is
    # less flexible. On the other, this flexibility might not be required
    # beyond specifically-defined subclasses.

    def __init__(self, **kwargs):
        """Initialize the digest with a dynamic subject."""
        super(ActivityDigest, self).__init__(**kwargs)
        self.subject = self.get_subject()

    def get_context_data(self, *args):
        """Adds classified activity to the context."""
        context = super(ActivityDigest, self).get_context_data(*args)
        context["activity"] = self.get_activity()
        context["subject"] = self.get_subject()
        return context

    def notifications_for_model(self, notifications, model):
        """Filter a list of notifications for a specific model,
        split between objects owned by the user and objects followed by the user."""
        user = self.get_user()
        model_notifications = notifications.for_model(model)
        own_model_actions = Action.objects.owned_by(user, model)
        own_model_notifications = model_notifications.filter(
            action__in=own_model_actions
        )
        following_model_notifications = model_notifications.exclude(
            action__in=own_model_actions
        )
        return {
            "count": model_notifications.count(),
            "mine": own_model_notifications,
            "following": following_model_notifications,
        }

    def get_activity(self):
        """Returns a list of activities to be sent in the email"""
        duration = self.get_duration()
        user = self.get_user()
        # get unread notifications for the user that are new since the last email
        notifications = (
            Notification.objects.for_user(user)
            .get_unread()
            .filter(datetime__gte=duration)
        )
        self.activity["requests"] = self.foia_notifications(notifications)
        self.activity["questions"] = self.notifications_for_model(
            notifications, Question
        )
        self.activity["count"] = (
            self.activity["requests"]["count"] + self.activity["questions"]["count"]
        )
        return self.activity

    def foia_notifications(self, notifications):
        """Do some heavy filtering and classifying of foia notifications."""
        filtered_notifications = self.notifications_for_model(
            notifications, FOIARequest
        )
        filtered_notifications["mine"] = self.classify_request_notifications(
            filtered_notifications["mine"],
            [
                ("completed", "completed"),
                ("rejected", "rejected"),
                ("no_documents", "no responsive documents"),
                ("require_payment", "payment"),
                ("require_fix", "require_fix"),
                ("interim_response", "processing"),
                ("acknowledged", "acknowledged"),
                ("received", "sent a communication"),
            ],
        )
        filtered_notifications["following"] = self.classify_request_notifications(
            filtered_notifications["following"],
            [
                ("completed", "completed"),
                ("rejected", "rejected"),
                ("no_documents", "no responsive documents"),
                ("require_payment", "payment"),
                ("require_fix", "require_fix"),
                ("interim_response", "processing"),
                ("acknowledged", "acknowledged"),
                ("received", "sent a communication"),
            ],
        )
        filtered_notifications["count"] = (
            filtered_notifications["mine"]["count"]
            + filtered_notifications["following"]["count"]
        )
        return filtered_notifications

    def classify_request_notifications(self, notifications, classifiers):
        """Break a single list of notifications into a classified dictionary."""
        classified = {}
        # a classifier should be a tuple of a key and a verb phrase to filter by
        # e.g. ('no_documents', 'no responsive documents')
        for classifier in classifiers:
            classified[classifier[0]] = notifications.filter(
                action__verb__icontains=classifier[1]
            )
        activity_count = 0
        for _, classified_stream in classified.items():
            activity_count += len(classified_stream)
        classified["count"] = activity_count
        return classified

    def get_subject(self):
        """Summarizes the activities in the notification."""
        count = self.activity["count"]
        subject = str(count) + " Update"
        if count > 1:
            subject += "s"
        return self.subject + ": " + subject

    def send(self, fail_silently=False):
        """Don't send the email if there's no activity."""
        if self.activity["count"] < 1:
            return 0
        return super(ActivityDigest, self).send(fail_silently)


class StaffDigest(Digest):
    """An email that digests other site stats for staff members."""

    text_template = "message/digest/staff_digest.txt"
    html_template = "message/digest/staff_digest.html"
    interval = relativedelta(days=1)

    class DataPoint:
        """Holds a data point for display in a digest."""

        def __init__(
            self,
            name,
            current_value,
            previous_value,
            previous_week_value,
            previous_month_value,
            growth=True,
        ):
            """Initialize the statistical object"""
            # pylint: disable=too-many-arguments
            self.name = name
            self.current = current_value
            if self.current and previous_value is not None:
                self.delta = self.current - previous_value
            else:
                self.delta = None
            if self.current and previous_week_value is not None:
                self.delta_week = self.current - previous_week_value
            else:
                self.delta_week = None
            if self.current and previous_month_value is not None:
                self.delta_month = self.current - previous_month_value
            else:
                self.delta_month = None
            self.growth = growth

    def get_trailing_cost(self, current, duration, cost_per):
        """Returns the trailing cost for communications over a period"""
        period = [current - relativedelta(days=duration), current]
        filters = Q(
            communication__datetime__range=period, communication__response=False
        )
        trailing = {
            "email": EmailCommunication.objects.filter(filters).count(),
            "fax": FaxCommunication.objects.filter(filters).count(),
            "mail": MailCommunication.objects.filter(filters).count(),
        }
        trailing_cost = {
            "email": trailing["email"] * cost_per["email"],
            "fax": trailing["fax"] * cost_per["fax"],
            "mail": trailing["mail"] * cost_per["mail"],
        }
        return trailing_cost

    def get_comms(self, start, end):
        """Returns communication data over a date range"""
        filters = Q(
            communication__datetime__range=[start, end], communication__response=False
        )
        delivered_by = {
            "email": EmailCommunication.objects.filter(filters).count(),
            "fax": FaxCommunication.objects.filter(filters).count(),
            "mail": MailCommunication.objects.filter(filters).count(),
        }
        cost_per = {"email": 0.00, "fax": 0.09, "mail": 0.54}
        cost = {
            "email": delivered_by["email"] * cost_per["email"],
            "fax": delivered_by["fax"] * cost_per["fax"],
            "mail": delivered_by["mail"] * cost_per["mail"],
        }
        received = FOIACommunication.objects.filter(
            datetime__range=[start, end], response=True
        )
        sent = FOIACommunication.objects.filter(
            datetime__range=[start, end], response=False
        )
        return {
            "sent": sent.count(),
            "received": received.count(),
            "delivery": {
                "format": delivered_by,
                "cost": cost_per,
                "expense": cost,
                "trailing": self.get_trailing_cost(end, 30, cost_per),
            },
        }

    def get_data(self, start, end):
        """Compares statistics between two dates"""
        try:
            current = Statistics.objects.get(date=end)
            previous = Statistics.objects.get(date=start)
            previous_week = Statistics.objects.get(date=end - relativedelta(weeks=1))
            previous_month = Statistics.objects.get(date=end - relativedelta(months=1))
        except Statistics.DoesNotExist:
            return None  # if statistics cannot be found, don't send anything
        data = {"request": [], "user": []}
        stats = [
            ("request", "Requests", "total_requests", True),
            ("request", "Pages", "total_pages", True),
            ("request", "Processing", "total_requests_submitted", False),
            ("request", "Processing Time", "requests_processing_days", False),
            ("request", "Flags", "total_unresolved_flagged_tasks", False),
            ("request", "Flags Time", "flag_processing_days", False),
            (
                "request",
                "Review Agency Tasks",
                "total_unresolved_reviewagency_tasks",
                False,
            ),
            ("user", "Users Filed", "total_users_filed", True),
            ("user", "Users", "total_users", True),
            ("user", "Pro Users", "pro_users", True),
            ("user", "Active Org Members", "total_active_org_members", True),
        ]
        for section, name, stat, growth in stats:
            data[section].append(
                self.DataPoint(
                    name,
                    getattr(current, stat),
                    getattr(previous, stat),
                    getattr(previous_week, stat),
                    getattr(previous_month, stat),
                    growth,
                )
            )
        return data

    def get_pro_users(self, start, end):
        """Compares pro users between two dates"""
        try:
            current = Statistics.objects.get(date=end)
            previous = Statistics.objects.get(date=start)
        except Statistics.DoesNotExist:
            return None  # if statistics cannot be found, don't send anything
        current_pro = current.pro_user_names
        if current_pro:
            current_pro = set(current_pro.split(";"))
        else:
            current_pro = set([])
        previous_pro = previous.pro_user_names
        if previous_pro:
            previous_pro = set(previous_pro.split(";"))
        else:
            previous_pro = set([])
        pro_gained = [
            User.objects.filter(username=username).first()
            for username in current_pro - previous_pro
        ]
        pro_gained = [u for u in pro_gained if u is not None]
        pro_lost = [
            User.objects.filter(username=username).first()
            for username in previous_pro - current_pro
        ]
        pro_lost = [u for u in pro_lost if u is not None]
        data = {"gained": pro_gained, "lost": pro_lost}
        return data

    def get_stale_tasks(self):
        """Get stale tasks"""
        # pylint: disable=import-outside-toplevel
        from muckrock.task.models import (
            NewAgencyTask,
            OrphanTask,
            FlaggedTask,
            PortalTask,
            SnailMailTask,
        )

        stale_tasks = OrderedDict()
        stale_tasks["Processing Requests"] = (
            FOIARequest.objects.filter(
                status="submitted", date_processing__lt=(date.today() - timedelta(5))
            )
            .order_by("date_processing")
            .annotate(days_old=ExtractDay(Now() - F("date_processing")))
        )[:5]
        task_types = [
            (NewAgencyTask, 3),
            (OrphanTask, 5),
            (FlaggedTask, 5),
            (PortalTask, 5),
            (SnailMailTask, 5),
        ]
        for task_type, days_old in task_types:
            stale_tasks[task_type.type] = (
                task_type.objects.filter(
                    date_created__lt=(timezone.now() - timedelta(days_old)),
                    resolved=False,
                )
                .order_by("date_created")
                .annotate(
                    days_old=ExtractDay(
                        Cast(Now() - F("date_created"), DurationField())
                    )
                )[:5]
            )
        return stale_tasks

    def get_crowdfunds(self):
        """Get crodfund information"""
        crowdfund_info = {}
        crowdfund_info["active"] = list(
            Crowdfund.objects.filter(closed=False).order_by("-date_due")
        )
        crowdfund_info["new"] = list(
            Crowdfund.objects.filter(date_created=date.today() - timedelta(1))
        )
        return crowdfund_info

    def get_projects(self):
        """Get project information"""
        # pylint: disable=import-outside-toplevel
        from muckrock.project.models import Project

        project_info = OrderedDict()
        project_info["Pending Projects"] = Project.objects.get_pending()
        project_info["Projects Created in the Past Week"] = Project.objects.filter(
            date_created__gte=date.today() - timedelta(7)
        )
        project_info["Projects Approved in the Past Week"] = Project.objects.filter(
            date_approved__gte=date.today() - timedelta(7)
        )
        return project_info

    def get_checks(self):
        """Get checks sent or deposited"""
        yesterday = date.today() - timedelta(1)
        checks = {}
        checks["created"] = Check.objects.filter(created_datetime__date=yesterday)
        checks["deposited"] = Check.objects.filter(status_date=yesterday)
        return checks

    def get_context_data(self, *args):
        """Adds classified activity to the context"""
        context = super(StaffDigest, self).get_context_data(*args)
        end = timezone.now() - self.interval
        start = end - self.interval
        context["stats"] = self.get_data(start, end)
        context["comms"] = self.get_comms(start, end)
        context["pro_users"] = self.get_pro_users(end - relativedelta(days=5), end)
        context["stale_tasks"] = self.get_stale_tasks()
        context["stale_tasks_show"] = any(i for i in context["stale_tasks"].values())
        context["crowdfunds"] = self.get_crowdfunds()
        context["projects"] = self.get_projects()
        context["checks"] = self.get_checks()
        return context

    def send(self, fail_silently=False):
        """Don't send to users who are not staff"""
        user = self.get_user()
        if not user.is_staff:
            return 0
        return super(StaffDigest, self).send(fail_silently)
