"""
Dashing widgets for the dashboard
"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, DurationField, F, Sum
from django.db.models.functions import Cast, Now

# Standard Library
import json
from calendar import monthrange
from datetime import date

# Third Party
from constance import config
from dashing.widgets import GraphWidget, ListWidget, NumberWidget, Widget
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
from smart_open.smart_open_lib import smart_open

# MuckRock
from muckrock.accounts.models import Statistics
from muckrock.accounts.utils import user_entitlement_count
from muckrock.core.models import ExtractDay
from muckrock.core.utils import cache_get_or_set
from muckrock.crowdsource.models import CrowdsourceResponse
from muckrock.foia.models import FOIAFile, FOIARequest
from muckrock.project.models import Project
from muckrock.task.models import FlaggedTask, ReviewAgencyTask

RED = "#dc5945"
GREEN = "#96bf48"
BLUE = "#12b0c5"

# Widgets to inherit from


def cmp(x, y):
    """
    Replacement for built-in function cmp that was removed in Python 3

    Compare the two objects x and y and return an integer according to
    the outcome. The return value is negative if x < y, zero if x == y
    and strictly positive if x > y.
    """
    # pylint: disable=invalid-name

    return (x > y) - (x < y)


class CompareNumberWidget(NumberWidget):
    """A number widget which compares to a previous value"""

    percent = False

    def get_context(self):
        """Get data to pass to javascript"""
        value = self.get_value()
        previous = self.get_previous_value()
        value = 0 if value is None else value
        previous = 0 if previous is None else previous
        delta = value - previous
        if self.percent and previous != 0:
            delta = (100 * delta) / previous
            delta = "{}%".format(delta)
        else:
            delta = "{:,}".format(delta)
        comp = cmp(value, previous)
        if comp == 0:
            color = BLUE
        elif comp == self.direction:
            color = GREEN
        else:
            color = RED

        if comp == -1:
            icon = "fa fa-arrow-down"
        elif comp == 1:
            icon = "fa fa-arrow-up"
        else:
            icon = ""

        return {
            "value": "{:,}".format(value),
            "detail": delta,
            "color": color,
            "icon": icon,
            "title": self.get_title(),
            "moreInfo": self.get_more_info(),
        }


class GoalCompareNumberWidget(CompareNumberWidget):
    """A number widget based on a goal that grows month over month"""

    direction = 1

    def get_previous_value(self):
        """Calculate the goal for this point of the month"""
        today = date.today()
        _, days = monthrange(today.year, today.month)
        return int(round(self._goal() * (float(today.day) / days)))

    def get_more_info(self):
        """Show the goal"""
        return "{:,} monthly goal".format(self._goal())

    def _goal(self):
        """Calculate the goal for the month"""
        today = date.today()
        num_months = (today.year - self.goal_start.year) * 12 + (
            today.month - self.goal_start.month
        )
        return int(self.goal_initial * (self.goal_growth ** num_months))


class StatGraphWidget(GraphWidget):
    """Graph based on stats history"""

    days = 30

    def get_data(self):
        """Get graph data"""
        stats = Statistics.objects.all()[: self.days : -1]
        return [{"x": i, "y": getattr(stat, self.stat)} for i, stat in enumerate(stats)]


# Concrete widgets


class ProcessingDaysWidget(CompareNumberWidget):
    """Show how many processing days"""

    title = "Processing Days"
    direction = -1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_processing_days()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest("date").requests_processing_days


class ProcessingCountWidget(CompareNumberWidget):
    """Show how many processing requests there are"""

    title = "Processing"
    direction = -1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.filter(status="submitted").count()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest("date").total_requests_submitted


class OldestProcessingWidget(ListWidget):
    """Show the oldest processing requests"""

    title = "Oldest Processing"

    def get_data(self):
        """Get the oldest processing requests"""
        requests = (
            FOIARequest.objects.filter(status="submitted")
            .annotate(days=date.today() - F("date_processing"))
            .order_by("-days")
            .values("title", "days")[:5]
        )
        return [
            {
                "label": r["title"]
                if len(r["title"]) < 28
                else "{}...".format(r["title"][:28]),
                "value": r["days"],
            }
            for r in requests
        ]


class ProcessingGraphWidget(StatGraphWidget):
    """Graph of processing days"""

    title = "Processing Days"
    stat = "requests_processing_days"

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_processing_days()


class FlagDaysWidget(CompareNumberWidget):
    """Show how many flag processing days"""

    title = "Flags Days"
    direction = -1

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.get_processing_days()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest("date").flag_processing_days


class FlagCountWidget(CompareNumberWidget):
    """Show how many open flag tasks there are"""

    title = "Flags"
    direction = -1

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.filter(resolved=False).get_undeferred().count()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest("date").total_unresolved_flagged_tasks


class OldestFlagWidget(ListWidget):
    """Show the oldest flag tasks"""

    title = "Oldest Flags"

    def get_data(self):
        """Get the oldest flag tasks"""
        tasks = (
            FlaggedTask.objects.filter(resolved=False)
            .get_undeferred()
            .annotate(days=ExtractDay(Cast(Now() - F("date_created"), DurationField())))
            .order_by("-days")
            .values("text", "days")[:5]
        )
        return [
            {
                "label": t["text"]
                if len(t["text"]) < 28
                else "{}...".format(t["text"][:28]),
                "value": t["days"],
            }
            for t in tasks
        ]


class FlagGraphWidget(StatGraphWidget):
    """Graph of flag days"""

    title = "Flag Days"
    stat = "flag_processing_days"

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.get_processing_days()


class ProUserGraphWidget(StatGraphWidget):
    """Graph of pro users"""

    title = "Pro Users"
    stat = "pro_users"

    def get_value(self):
        """Get value"""
        return user_entitlement_count("professional")


class ReviewAgencyGraphWidget(StatGraphWidget):
    """Graph of review agency tasks"""

    title = "Review Agency Tasks"
    stat = "total_unresolved_reviewagency_tasks"

    def get_value(self):
        """Get value"""
        return ReviewAgencyTask.objects.filter(resolved=False).get_undeferred().count()


class RequestsFiledGraphWidget(GraphWidget):
    """Graph of requests filed"""

    title = "Daily Requests Filed"
    days = 30

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_today().count()

    def get_data(self):
        """Get graph data"""
        stats = Statistics.objects.all()[: self.days : -1]
        return [
            {
                "x": i,
                "y": sum(
                    [
                        stat.daily_requests_pro,
                        stat.daily_requests_basic,
                        stat.daily_requests_beta,
                        stat.daily_requests_proxy,
                        stat.daily_requests_admin,
                        stat.daily_requests_org,
                    ]
                ),
            }
            for i, stat in enumerate(stats)
        ]


class CrowdsourceRespondedUsersGraphWidget(StatGraphWidget):
    """Graph of how many users have responded to any crowdsource"""

    title = "Users Who Completed an Assignment"
    stat = "num_crowdsource_responded_users"

    def get_value(self):
        """Get value"""
        return CrowdsourceResponse.objects.aggregate(Count("user", distinct=True))[
            "user__count"
        ]


class CrowdsourceResponsesGraphWidget(StatGraphWidget):
    """Graph of total crowdsource responses"""

    title = "Total Completed Assignments"
    stat = "total_crowdsource_responses"

    def get_value(self):
        """Get value"""
        return CrowdsourceResponse.objects.count()


class RequestsFiledWidget(CompareNumberWidget):
    """Number of requests filed today"""

    title = "Requests Filed Today"
    direction = 1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_today().count()

    def get_previous_value(self):
        """Get previous value"""
        stat = Statistics.objects.latest("date")
        return sum(
            [
                stat.daily_requests_pro,
                stat.daily_requests_basic,
                stat.daily_requests_beta,
                stat.daily_requests_proxy,
                stat.daily_requests_admin,
                stat.daily_requests_org,
            ]
        )


class RequestsSuccessWidget(CompareNumberWidget):
    """Number of total succesful requests"""

    title = "Total Succesful Requests"
    direction = 1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.filter(status="done").count()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest("date").total_requests_success


class ProUserCountWidget(CompareNumberWidget):
    """Show how many Pro Users we have"""

    title = "Pro Users"
    direction = 1
    more_info = "vs one month ago"

    def get_value(self):
        """Get value"""
        return user_entitlement_count("professional")

    def get_previous_value(self):
        """Get previous value"""
        # get 30th newest stat ~1 month ago
        stat = list(Statistics.objects.all()[:30])[-1]
        return stat.pro_users


class OrgUserCountWidget(CompareNumberWidget):
    """Show how many Org Users we have"""

    title = "Org Users"
    direction = 1
    more_info = "vs one month ago"

    def get_value(self):
        """Get value"""
        return user_entitlement_count("organization")

    def get_previous_value(self):
        """Get previous value"""
        # get 30th newest stat ~1 month ago
        stat = list(Statistics.objects.all()[:30])[-1]
        return stat.total_active_org_members


class RecentRequestsWidget(ListWidget):
    """Show the latest submitted requests"""

    title = "Recently Submitted Requests"

    def get_data(self):
        """Get the oldest processing requests"""
        requests = (
            FOIARequest.objects.get_public()
            .exclude(composer__datetime_submitted=None)
            .order_by("-composer__datetime_submitted")
            .values("title")[:4]
        )
        return [{"label": r["title"]} for r in requests]


class PageCountWidget(CompareNumberWidget):
    """Show how many pages have been released"""

    title = "Total Pages Released"
    direction = 1

    def get_value(self):
        """Get value"""
        return FOIAFile.objects.aggregate(Sum("pages"))["pages__sum"]

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest("date").total_pages


class RegisteredUsersWidget(GoalCompareNumberWidget):
    """Show month over month registered user rate growth"""

    title = "New Registered Users"

    def __init__(self, *args, **kwargs):
        super(RegisteredUsersWidget, self).__init__(*args, **kwargs)
        self.goal_initial = config.NEW_USER_GOAL_INIT
        self.goal_growth = config.NEW_USER_GOAL_GROWTH
        self.goal_start = config.NEW_USER_START_DATE

    def get_value(self):
        """Get how many new users have registered this month"""
        month_start = date.today().replace(day=1)
        return (
            User.objects.filter(date_joined__gte=month_start)
            .filter(profile__agency=None)
            .count()
        )


class PageViewsWidget(NumberWidget):
    """Show page view data"""

    title = "Page Views"

    def __init__(self, *args, **kwargs):
        super(PageViewsWidget, self).__init__(*args, **kwargs)
        self.goal_initial = config.PAGE_VIEWS_GOAL_INIT
        self.goal_growth = config.PAGE_VIEWS_GOAL_GROWTH
        self.goal_start = config.PAGE_VIEWS_START_DATE

    def get_value(self):
        """Get the page views so far for this month"""

        def inner():
            """Inner function for caching"""
            today = date.today()
            month_start = today.replace(day=1)

            # initalize google analytics api
            # we store the keyfile on s3
            key = f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/google/analytics_key.json"
            with smart_open(key) as key_file:
                credentials = ServiceAccountCredentials.from_json_keyfile_dict(
                    json.loads(key_file.read()),
                    ["https://www.googleapis.com/auth/analytics.readonly"],
                )
            try:
                analytics = build(
                    "analyticsreporting",
                    "v4",
                    credentials=credentials,
                    cache_discovery=False,
                )
                response = (
                    analytics.reports()
                    .batchGet(
                        body={
                            "reportRequests": [
                                {
                                    "viewId": settings.VIEW_ID,
                                    "dateRanges": [
                                        {
                                            "startDate": month_start.isoformat(),
                                            "endDate": today.isoformat(),
                                        }
                                    ],
                                    "metrics": [{"expression": "ga:pageviews"}],
                                }
                            ]
                        }
                    )
                    .execute()
                )
            except HttpError:
                return "Error"
            try:
                # google really buries the useful data in the response
                # remove format if we want to go back to a comparison
                return "{:,}".format(
                    int(
                        response["reports"][0]["data"]["rows"][0]["metrics"][0][
                            "values"
                        ][0]
                    )
                )
            except KeyError:
                return "Error"

        return cache_get_or_set("dashboard:pageviews", inner, 60 * 5)


class ProjectCountWidget(NumberWidget):
    """Show quarterly project count"""

    title = "Quarterly Projects"

    def get_value(self):
        """Projects since the beginning of the quarter"""
        today = date.today()
        month = today.month
        quarter_month = month - (month - 1) % 3
        quarter_start = today.replace(month=quarter_month, day=1)
        return Project.objects.filter(
            approved=True, date_created__gte=quarter_start
        ).count()

    def get_detail(self):
        """Total approved projects"""
        return "Total: {:,}".format(Project.objects.count())


# Top level widget to pull them all together into one request


class TopWidget(Widget):
    """Top level widget
    This allows all widgets to be updated with only one HTTP request
    """

    def __init__(self, *args, **kwargs):
        super(TopWidget, self).__init__(*args, **kwargs)
        self.widgets = [
            ProcessingCountWidget(),
            OldestProcessingWidget(),
            ProcessingGraphWidget(),
            FlagCountWidget(),
            OldestFlagWidget(),
            FlagGraphWidget(),
            ProUserCountWidget(),
            OrgUserCountWidget(),
            RecentRequestsWidget(),
            RegisteredUsersWidget(),
            ReviewAgencyGraphWidget(),
            RequestsFiledGraphWidget(),
            RequestsSuccessWidget(),
            CrowdsourceRespondedUsersGraphWidget(),
            CrowdsourceResponsesGraphWidget(),
            PageViewsWidget(),
            ProjectCountWidget(),
        ]

    def get_context(self):
        """Return data for all widgets"""
        context = {}
        for widget in self.widgets:
            context[widget.__class__.__name__] = widget.get_context()
        return context
