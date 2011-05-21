"""
Admin registration for tag models
"""

from django.contrib import admin

from taggit.models import Tag as TaggitTag

from tags.models import Tag

class TagAdmin(admin.ModelAdmin):
    """Model Admin for a tag"""
    # pylint: disable-msg=R0904

    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'user')
    list_filter = ['user']

admin.site.register(Tag, TagAdmin)
admin.site.unregister(TaggitTag)
