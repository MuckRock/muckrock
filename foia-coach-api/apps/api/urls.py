"""
URL Configuration for FOIA Coach API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .viewsets import (
    JurisdictionViewSet,
    JurisdictionResourceViewSet,
    QueryViewSet,
)

# Create API router
router = DefaultRouter()
router.register(r'jurisdictions', JurisdictionViewSet, basename='jurisdiction')
router.register(r'resources', JurisdictionResourceViewSet, basename='resource')
router.register(r'query', QueryViewSet, basename='query')

app_name = 'api'

urlpatterns = [
    path('v1/', include(router.urls)),
]
