"""
URL mappings for the Task application
"""

from django.conf.urls import patterns, url
from muckrock.task import views

urlpatterns = patterns(
    '',
    url(r'^$', views.TaskList.as_view(), name='task-list'),
    url(r'^inbox/$', views.InboxTaskList.as_view(), name='task-list-inbox'),
    url(r'^unassigned/$', views.UnassignedTaskList.as_view(), name='task-list-unassigned'),
    url(r'^resolved/$', views.ResolvedTaskList.as_view(), name='task-list-resolved'),
    url(r'^assign/$', views.assign, name='task-assign'),
)
