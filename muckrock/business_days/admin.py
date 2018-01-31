"""
Admin registration for business day models
"""

# Django
from django.contrib import admin

# MuckRock
from muckrock.business_days.models import Holiday

admin.site.register(Holiday)
