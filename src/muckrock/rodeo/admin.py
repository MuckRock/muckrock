"""
Admin registration for Rodeo models
"""

from django.contrib import admin

from rodeo.models import Rodeo, RodeoOption, RodeoVote

# These inhereit more than the allowed number of public methods
# pylint: disable-msg=R0904

class RodeoOptionInline(admin.TabularInline):
    """Rodeo Option Inline admin options"""
    model = RodeoOption
    extra = 3

class RodeoAdmin(admin.ModelAdmin):
    """Rodeo Admin"""
    list_display = ('title', 'document')
    inlines = [RodeoOptionInline]

admin.site.register(Rodeo, RodeoAdmin)
admin.site.register(RodeoVote)
