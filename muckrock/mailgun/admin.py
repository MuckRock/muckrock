"""
Admin registration for Tasks
"""

from django.contrib import admin

from muckrock.mailgun.models import WhitelistDomain

admin.site.register(WhitelistDomain)
