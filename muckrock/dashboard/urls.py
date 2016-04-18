"""
URL mappings for the Dashboard application
"""

from django.conf.urls import url

from muckrock.dashboard import views

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^data\.json$', views.dashboard_data, name='dashboard-data'),
]
