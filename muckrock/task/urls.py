"""
URL mappings for the Task application
"""

from django.conf.urls import patterns, url

# pylint: disable=unused-import
import muckrock.task.signals
# pylint: enable=unused-import
from muckrock.task import views

urlpatterns = patterns(
    '',
    url(r'^$', views.TaskList.as_view(), name='task-list'),
    url(r'^orphan/$', views.OrphanTaskList.as_view(), name='orphan-task-list'),
    url(r'^snail-mail/$', views.SnailMailTaskList.as_view(), name='snail-mail-task-list'),
    url(r'^rejected-email/$',
        views.RejectedEmailTaskList.as_view(),
        name='rejected-email-task-list'),
    url(r'^stale-agency/$', views.StaleAgencyTaskList.as_view(), name='stale-agency-task-list'),
    url(r'^flagged/$', views.FlaggedTaskList.as_view(), name='flagged-task-list'),
    url(r'^new-agency/$', views.NewAgencyTaskList.as_view(), name='new-agency-task-list'),
    url(r'^response/$', views.ResponseTaskList.as_view(), name='response-task-list'),
    url(r'^status-change/$', views.StatusChangeTaskList.as_view(), name='status-change-task-list'),
    url(r'^crowdfund/$', views.CrowdfundTaskList.as_view(), name='crowdfund-task-list'),
    url(r'^multirequest/$', views.MultiRequestTaskList.as_view(), name='multirequest-task-list'),
    url(r'^failed-fax/$', views.FailedFaxTaskList.as_view(), name='failed-fax-task-list'),
    # tasks for a specific request
    url(r'^request/(?P<pk>\d+)/$', views.RequestTaskList.as_view(), name='request-task-list')
)
