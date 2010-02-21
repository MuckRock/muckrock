"""
Admin registration for accounts models
"""

from django.contrib import admin
from accounts.models import Profile

admin.site.register(Profile)

