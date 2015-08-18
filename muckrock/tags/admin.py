"""
Admin registration for tag models
"""

from django.contrib import admin

from taggit.models import Tag as TaggitTag

from muckrock.tags.models import Tag

class TagAdmin(admin.ModelAdmin):
    """Model Admin for a tag"""
    # pylint: disable=too-many-public-methods

    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name']

admin.site.register(Tag, TagAdmin)
admin.site.unregister(TaggitTag)
