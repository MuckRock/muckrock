"""
URL mappings for the communicaiton app
"""

# Django
from django.conf.urls import url

# MuckRock
from muckrock.communication import views

urlpatterns = [
    url(
        r'emailaddress/(?P<idx>\d+)/$',
        views.EmailDetailView.as_view(),
        name='email-detail'
    ),
    url(
        r'phonenumber/(?P<idx>\d+)/$',
        views.PhoneDetailView.as_view(),
        name='phone-detail'
    ),
]
