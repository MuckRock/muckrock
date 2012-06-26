"""
Admin registration for business day models
"""

from django.contrib import admin

# XXX
from muckrock.business_days.models import Holiday

admin.site.register(Holiday)
