"""
URL mappings for the data set application
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.dataset import views

urlpatterns = [
    url(
        r'^view/(?P<slug>[-\w\d]+)-(?P<idx>\d+)/$',
        views.detail,
        name='dataset-detail',
    ),
    url(
        r'^embed/(?P<slug>[-\w\d]+)-(?P<idx>\d+)/$',
        views.embed,
        name='dataset-embed',
    ),
    url(
        r'^data/(?P<slug>[-\w\d]+)-(?P<idx>\d+)/$',
        views.data,
        name='dataset-data',
    ),
    url(
        r'^create/$',
        views.create,
        name='dataset-create',
    ),
]
