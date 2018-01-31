"""
Admin registration for Tasks
"""

# Django
from django.contrib import admin

# MuckRock
from muckrock.mailgun.models import WhitelistDomain

admin.site.register(WhitelistDomain)
