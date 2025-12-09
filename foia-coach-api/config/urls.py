"""
URL configuration for FOIA Coach API service.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # API routes will be added in Phase 5
    # path('api/', include('apps.api.urls')),
]
