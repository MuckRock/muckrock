"""
Admin registration for news models
"""

from django.contrib import admin

from news.models import Article

class ArticleAdmin(admin.ModelAdmin):
    """Model Admin for a news article"""
    # pylint: disable-msg=R0904

    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'author', 'pub_date', 'publish')
    list_filter = ['pub_date']
    date_hierarchy = 'pub_date'
    search_fields = ['title', 'body']

admin.site.register(Article, ArticleAdmin)

