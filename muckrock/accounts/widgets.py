"""
Dashing widgets for the dashboard
"""

# Django
from django.db.models import F, Sum
from django.db.models.functions import ExtractDay, Now

# Standard Library
from datetime import date

# Third Party
from dashing.widgets import GraphWidget, ListWidget, NumberWidget, Widget

# MuckRock
from muckrock.accounts.models import Profile, Statistics
from muckrock.foia.models import FOIAFile, FOIARequest
from muckrock.task.models import FlaggedTask

RED = '#dc5945'
GREEN = '#96bf48'
BLUE = '#12b0c5'

# Widgets to inherit from


class CompareNumberWidget(NumberWidget):
    """A number widget which compares to a previous value"""

    def get_context(self):
        """Get data to pass to javascript"""
        value = self.get_value()
        previous = self.get_previous_value()
        delta = value - previous
        comp = cmp(value, previous)
        if comp == 0:
            color = BLUE
        elif comp == self.direction:
            color = GREEN
        else:
            color = RED

        if comp == -1:
            icon = 'fa fa-arrow-down'
        elif comp == 1:
            icon = 'fa fa-arrow-up'
        else:
            icon = ''

        return {
            'value': u'{:,}'.format(value),
            'detail': u'{:+,}'.format(delta),
            'color': color,
            'icon': icon,
            'title': self.get_title(),
            'moreInfo': self.get_more_info(),
        }


class StatGraphWidget(GraphWidget):
    """Graph based on stats history"""
    days = 30

    def get_data(self):
        """Get graph data"""
        stats = Statistics.objects.all()[:self.days:-1]
        return [{
            'x': i,
            'y': getattr(stat, self.stat)
        } for i, stat in enumerate(stats)]


# Concrete widgets


class ProcessingDaysWidget(CompareNumberWidget):
    """Show how many processing days"""
    title = 'Processing Days'
    direction = -1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_processing_days()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest('date').requests_processing_days


class ProcessingCountWidget(CompareNumberWidget):
    """Show how many processing requests there are"""
    title = 'Processing'
    direction = -1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.filter(status='submitted').count()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest('date').total_requests_submitted


class OldestProcessingWidget(ListWidget):
    """Show the oldest processing requests"""
    title = 'Oldest Processing'

    def get_data(self):
        """Get the oldest processing requests"""
        requests = (
            FOIARequest.objects.filter(status='submitted')
            .annotate(days=date.today() - F('date_processing'))
            .order_by('-days').values('title', 'days')[:5]
        )
        return [{
            'label':
                r['title']
                if len(r['title']) < 28 else u'{}...'.format(r['title'][:28]),
            'value':
                r['days'],
        } for r in requests]


class ProcessingGraphWidget(StatGraphWidget):
    """Graph of processing days"""
    title = 'Processing Days'
    stat = 'requests_processing_days'

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_processing_days()


class FlagDaysWidget(CompareNumberWidget):
    """Show how many flag processing days"""
    title = 'Flags Days'
    direction = -1

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.get_processing_days()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest('date').flag_processing_days


class FlagCountWidget(CompareNumberWidget):
    """Show how many open flag tasks there are"""
    title = 'Flags'
    direction = -1

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.filter(resolved=False).count()

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest('date').total_unresolved_flagged_tasks


class OldestFlagWidget(ListWidget):
    """Show the oldest flag tasks"""
    title = 'Oldest Flags'

    def get_data(self):
        """Get the oldest processing requests"""
        tasks = (
            FlaggedTask.objects.filter(resolved=False)
            .annotate(days=ExtractDay(Now() - F('date_created')))
            .order_by('-days').values('text', 'days')[:5]
        )
        return [{
            'label':
                t['text']
                if len(t['text']) < 28 else u'{}...'.format(t['text'][:28]),
            'value':
                t['days'],
        } for t in tasks]


class FlagGraphWidget(StatGraphWidget):
    """Graph of flag days"""
    title = 'Flag Days'
    stat = 'flag_processing_days'

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.get_processing_days()


class ProUserGraphWidget(StatGraphWidget):
    """Graph of pro users"""
    title = 'Pro Users'
    stat = 'pro_users'

    def get_value(self):
        """Get value"""
        return Profile.objects.filter(acct_type='pro').count()


class RequestsFiledWidget(CompareNumberWidget):
    """Number of requests filed today"""
    title = 'Requests Filed Today'
    direction = 1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.filter(date_submitted=date.today()).count()

    def get_previous_value(self):
        """Get previous value"""
        stat = Statistics.objects.latest('date')
        return sum([
            stat.daily_requests_pro,
            stat.daily_requests_basic,
            stat.daily_requests_beta,
            stat.daily_requests_proxy,
            stat.daily_requests_admin,
            stat.daily_requests_org,
        ])


class ProUserCountWidget(CompareNumberWidget):
    """Show how many Pro Users we have"""
    title = 'Pro Users'
    direction = 1
    more_info = 'vs one month ago'

    def get_value(self):
        """Get value"""
        return Profile.objects.filter(acct_type='pro').count()

    def get_previous_value(self):
        """Get previous value"""
        # get 30th newest stat ~1 month ago
        stat = list(Statistics.objects.all()[:30])[-1]
        return stat.pro_users


class OrgUserCountWidget(CompareNumberWidget):
    """Show how many Org Users we have"""
    title = 'Org Users'
    direction = 1
    more_info = 'vs one month ago'

    def get_value(self):
        """Get value"""
        return (
            Profile.objects.filter(
                organization__active=True,
                organization__monthly_cost__gt=0,
            ).count()
        )

    def get_previous_value(self):
        """Get previous value"""
        # get 30th newest stat ~1 month ago
        stat = list(Statistics.objects.all()[:30])[-1]
        return stat.total_active_org_members


class RecentRequestsWidget(ListWidget):
    """Show the latest submitted requests"""
    title = 'Recently Submitted Requests'

    def get_data(self):
        """Get the oldest processing requests"""
        requests = (
            FOIARequest.objects.get_submitted().get_public()
            .order_by('-date_submitted').values('title')[:15]
        )
        return [{
            'label':
                r['title']
                if len(r['title']) < 32 else u'{}...'.format(r['title'][:32]),
        } for r in requests]


class PageCountWidget(CompareNumberWidget):
    """Show how many pages have been released"""
    title = 'Total Pages Released'
    direction = 1

    def get_value(self):
        """Get value"""
        return FOIAFile.objects.aggregate(Sum('pages'))['pages__sum']

    def get_previous_value(self):
        """Get previous value"""
        return Statistics.objects.latest('date').total_pages


# Top level widget to pull them all together into one request


class TopWidget(Widget):
    """Top level widget
    This allows all widgets to be updated with only one HTTP request
    """
    widgets = [
        ProcessingCountWidget(),
        OldestProcessingWidget(),
        ProcessingGraphWidget(),
        FlagCountWidget(),
        OldestFlagWidget(),
        FlagGraphWidget(),
        ProUserGraphWidget(),
        RequestsFiledWidget(),
        ProUserCountWidget(),
        OrgUserCountWidget(),
        RecentRequestsWidget(),
        PageCountWidget(),
    ]

    def get_context(self):
        """Return data for all widgets"""
        context = {}
        for widget in self.widgets:
            context[widget.__class__.__name__] = widget.get_context()
        return context
