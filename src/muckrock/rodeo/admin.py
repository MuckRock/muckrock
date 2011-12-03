"""
Admin registration for Rodeo models
"""

from django.conf.urls.defaults import patterns, url
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

import csv

from rodeo.models import Rodeo, RodeoOption, RodeoVote

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class RodeoOptionInline(admin.TabularInline):
    """Rodeo Option Inline admin options"""
    model = RodeoOption
    extra = 3

class RodeoAdmin(admin.ModelAdmin):
    """Rodeo Admin"""
    list_display = ('title', 'document')
    inlines = [RodeoOptionInline]

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(RodeoAdmin, self).get_urls()
        my_urls = patterns('', url(r'^(?P<rodeo_pk>\d+)/votes\.csv$',
                                   self.admin_site.admin_view(self.csv),
                                   name='votes-csv'))
        return my_urls + urls

    def csv(self, request, rodeo_pk):
        """Create a CSV file of votes for a rodeo"""
        # pylint: disable=R0201
        # pylint: disable=W0613
        rodeo = get_object_or_404(Rodeo, pk=rodeo_pk)

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=votes.csv'

        writer = csv.writer(response)
        writer.writerow(['User', 'Page', 'Vote'])
        for vote in rodeo.get_votes():
            name = vote.user.username if vote.user is not None else 'Anonymous Coward'
            writer.writerow([name, vote.page, vote.option.title])

        return response

admin.site.register(Rodeo, RodeoAdmin)
admin.site.register(RodeoVote)
