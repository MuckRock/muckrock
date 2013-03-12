"""
Admin registration for news models
"""

from django.contrib import admin

from muckrock.news.models import Article, Photo

class ArticleAdmin(admin.ModelAdmin):
    """Model Admin for a news article"""
    # pylint: disable=R0904

    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'author', 'pub_date', 'publish')
    list_filter = ['pub_date']
    date_hierarchy = 'pub_date'
    search_fields = ['title', 'body']

admin.site.register(Article, ArticleAdmin)
admin.site.register(Photo)

