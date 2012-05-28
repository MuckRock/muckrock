"""
Admin registration for accounts models
"""

from django.conf.urls.defaults import patterns, url
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.http import HttpResponse

import csv

from accounts.models import Profile, Statistics

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class StatisticsAdmin(admin.ModelAdmin):
    """Statistics admin options"""
    list_display = ('date', 'total_requests', 'total_requests_success', 'total_requests_denied',
                    'total_pages', 'total_users', 'total_agencies', 'total_fees')

    def get_urls(self):
        """Add custom URLs here"""
        urls = super(StatisticsAdmin, self).get_urls()
        my_urls = patterns('', url(r'^stats\.csv$', self.admin_site.admin_view(self.csv),
                                   name='stats-csv'))
        return my_urls + urls

    def csv(self, request):
        """Create a CSV file of all the statistics"""
        # pylint: disable=R0201
        # pylint: disable=W0613
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=stats.csv'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Total Requests', 'Total successful requests',
                         'Total denied requests', 'Total pages', 'Total users',
                         'Users logged in today', 'Total agencies', 'Total fees'])
        for stat in Statistics.objects.all():
            writer.writerow([stat.date, stat.total_requests, stat.total_requests_success,
                             stat.total_requests_denied, stat.total_pages, stat.total_users,
                             ','.join(str(user) for user in stat.users_today.all()),
                             stat.total_agencies, stat.total_fees])

        return response


class ProfileAdmin(admin.ModelAdmin):
    """Profile admin options"""
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

admin.site.register(Statistics, StatisticsAdmin)
admin.site.register(Profile, ProfileAdmin)

UserAdmin.list_display += ('date_joined',)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
