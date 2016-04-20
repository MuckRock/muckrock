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
    url(r'^orphan/(?P<pk>\d+)/$', views.OrphanTaskList.as_view(), name='orphan-task'),
    url(r'^snail-mail/$', views.SnailMailTaskList.as_view(), name='snail-mail-task-list'),
    url(r'^snail-mail/(?P<pk>\d+)/$', views.SnailMailTaskList.as_view(), name='snail-mail-task'),
    url(r'^rejected-email/$',
        views.RejectedEmailTaskList.as_view(),
        name='rejected-email-task-list'),
    url(r'^rejected-email/(?P<pk>\d+)/$',
        views.RejectedEmailTaskList.as_view(),
        name='rejected-email-task'),
    url(r'^stale-agency/$',
        views.StaleAgencyTaskList.as_view(),
        name='stale-agency-task-list'),
    url(r'^stale-agency/(?P<pk>\d+)/$',
        views.StaleAgencyTaskList.as_view(),
        name='stale-agency-task'),
    url(r'^flagged/$', views.FlaggedTaskList.as_view(), name='flagged-task-list'),
    url(r'^flagged/(?P<pk>\d+)/$', views.FlaggedTaskList.as_view(), name='flagged-task'),
    url(r'^new-agency/$', views.NewAgencyTaskList.as_view(), name='new-agency-task-list'),
    url(r'^new-agency/(?P<pk>\d+)/$', views.NewAgencyTaskList.as_view(), name='new-agency-task'),
    url(r'^response/$', views.ResponseTaskList.as_view(), name='response-task-list'),
    url(r'^response/(?P<pk>\d+)/$', views.ResponseTaskList.as_view(), name='response-task'),
    url(r'^status-change/$', views.StatusChangeTaskList.as_view(), name='status-change-task-list'),
    url(r'^status-change/(?P<pk>\d+)/$',
        views.StatusChangeTaskList.as_view(),
        name='status-change-task'),
    url(r'^crowdfund/$', views.CrowdfundTaskList.as_view(), name='crowdfund-task-list'),
    url(r'^crowdfund/(?P<pk>\d+)/$',
        views.CrowdfundTaskList.as_view(),
        name='crowdfund-task'),
    url(r'^multirequest/$',
        views.MultiRequestTaskList.as_view(),
        name='multirequest-task-list'),
    url(r'^multirequest/(?P<pk>\d+)/$',
        views.MultiRequestTaskList.as_view(),
        name='multirequest-task'),
    url(r'^failed-fax/$', views.FailedFaxTaskList.as_view(), name='failed-fax-task-list'),
    url(r'^failed-fax/(?P<pk>\d+)/$', views.FailedFaxTaskList.as_view(), name='failed-fax-task'),
    url(r'^project-review/$', views.ProjectReviewTaskList.as_view(), name='projectreview-task-list'),
    url(r'^project-review/(?P<pk>\d+)/$', views.ProjectReviewTaskList.as_view(), name='projectreview-task'),
    # tasks for a specific request
    url(r'^request/(?P<pk>\d+)/$', views.RequestTaskList.as_view(), name='request-task-list')
)
