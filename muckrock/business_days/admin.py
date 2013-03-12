"""
Admin registration for business day models
"""

from django.contrib import admin

from muckrock.business_days.models import Holiday

admin.site.register(Holiday)
