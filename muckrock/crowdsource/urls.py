"""
URL mappings for the crowdsource app
"""

from django.conf.urls import url

from muckrock.crowdsource import views

urlpatterns = [
        url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/$',
            views.CrowdsourceFormView.as_view(),
            name='crowdsource-detail',
            ),
        url(r'^$',
            views.CrowdsourceListView.as_view(),
            name='crowdsource-list',
            ),
        ]
