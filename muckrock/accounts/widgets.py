"""
Dashing widgets for the dashboard
"""

from django.db.models import F

from dashing.widgets import (
        NumberWidget,
        ListWidget,
        GraphWidget,
        )
from datetime import date

from muckrock.accounts.models import Statistics
from muckrock.foia.models import FOIARequest
from muckrock.models import ExtractDay, Now
from muckrock.task.models import FlaggedTask

RED = '#dc5945'
GREEN = '#96bf48'
BLUE = '#12b0c5'

# pylint: disable=no-self-use

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
                'value': unicode(value),
                'detail': u'{:+}'.format(delta),
                'color': color,
                'icon': icon,
                'title': self.get_title(),
                }


class ProcessingDaysWidget(CompareNumberWidget):
    """Show how many processing days"""
    title = 'Processing Days'
    direction = -1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_processing_days()

    def get_previous_value(self):
        """Get detail"""
        return Statistics.objects.latest('date').requests_processing_days


class ProcessingCountWidget(CompareNumberWidget):
    """Show how many processing requests there are"""
    title = 'Processing'
    direction = -1

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.filter(status='submitted').count()

    def get_previous_value(self):
        """Get detail"""
        return Statistics.objects.latest('date').total_requests_submitted


class OldestProcessingWidget(ListWidget):
    """Show the oldest processing requests"""
    title = 'Oldest Processing'

    def get_data(self):
        """Get the oldest processing requests"""
        requests = (FOIARequest.objects
                .filter(status='submitted')
                .annotate(days=date.today() - F('date_processing'))
                .order_by('-days')
                .values('title', 'days')
                [:5]
                )
        return [{
            'label': r['title'] if len(r['title']) < 28
            else u'{}...'.format(r['title'][:28]),
            'value': r['days'],
            }
            for r in requests]


class ProcessingGraphWidget(GraphWidget):
    """Graph of processing days"""
    title = 'Processing Days'

    def get_value(self):
        """Get value"""
        return FOIARequest.objects.get_processing_days()

    def get_data(self):
        """Get graph data"""
        stats = Statistics.objects.all()[:30:-1]
        return [{'x': i, 'y': stat.requests_processing_days}
                for i, stat in enumerate(stats)]


class FlagDaysWidget(CompareNumberWidget):
    """Show how many flag processing days"""
    title = 'Flags Days'
    direction = -1

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.get_processing_days()

    def get_previous_value(self):
        """Get detail"""
        return Statistics.objects.latest('date').flag_processing_days


class FlagCountWidget(CompareNumberWidget):
    """Show how many open flag tasks there are"""
    title = 'Flags'
    direction = -1

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.filter(resolved=False).count()

    def get_previous_value(self):
        """Get detail"""
        return Statistics.objects.latest('date').total_unresolved_flagged_tasks


class OldestFlagWidget(ListWidget):
    """Show the oldest flag tasks"""
    title = 'Oldest Flags'

    def get_data(self):
        """Get the oldest processing requests"""
        tasks = (FlaggedTask.objects
                .filter(resolved=False)
                .annotate(days=ExtractDay(Now() - F('date_created')))
                .order_by('-days')
                .values('text', 'days')
                [:5]
                )
        return [{
            'label': t['text'] if len(t['text']) < 28
            else u'{}...'.format(t['text'][:28]),
            'value': t['days'],
            }
            for t in tasks]


class FlagGraphWidget(GraphWidget):
    """Graph of flag days"""
    title = 'Flag Days'

    def get_value(self):
        """Get value"""
        return FlaggedTask.objects.get_processing_days()

    def get_data(self):
        """Get graph data"""
        stats = Statistics.objects.all()[:30:-1]
        return [{'x': i, 'y': stat.flag_processing_days}
                for i, stat in enumerate(stats)]
