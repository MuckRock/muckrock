"""
URL mappings for the Task application
"""

from django.conf.urls import patterns, url
from muckrock.task import views

urlpatterns = patterns(
    '',
    url(r'^$', views.TaskList.as_view(), name='task-list'),
    url(r'^assign/$', views.assign, name='task-assign'),
)
