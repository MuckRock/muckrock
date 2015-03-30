"""
URL mappings for the Task application
"""

from django.conf.urls import patterns, url
from muckrock.task import views

urlpatterns = patterns(
    '',
    url(r'^$', views.TaskList.as_view(), name='task-list'),
    url(r'^orphan/$', views.OrphanTaskList.as_view(), name='orphan-task-list'),
    url(r'^snail-mail/$', views.SnailMailTaskList.as_view(), name='snail-mail-task-list'),
    url(r'^rejected-email/$', views.RejectedEmailTaskList.as_view(), name='rejected-email-task-list'),
    url(r'^stale-agency/$', views.StaleAgencyTaskList.as_view(), name='stale-agency-task-list'),
    url(r'^flagged/$', views.FlaggedTaskList.as_view(), name='flagged-task-list'),
    url(r'^new-agency/$', views.NewAgencyTaskList.as_view(), name='new-agency-task-list'),
    url(r'^response/$', views.ResponseTaskList.as_view(), name='response-task-list'),
)
