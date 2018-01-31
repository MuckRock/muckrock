"""
Admin registration for tag models
"""

# Django
from django.contrib import admin

# Third Party
from taggit.models import Tag as TaggitTag

# MuckRock
from muckrock.tags.models import Tag


class TagAdmin(admin.ModelAdmin):
    """Model Admin for a tag"""
    # pylint: disable=too-many-public-methods

    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_display = ['name']


admin.site.register(Tag, TagAdmin)
admin.site.unregister(TaggitTag)
