"""
Admin registration for FOIA models
"""

from django.contrib import admin
from foia.models import FOIARequest

admin.site.register(FOIARequest)

