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

    def save_model(self, request, obj, form, change):
        """Attach user to article on save"""

        obj.author = request.user
        obj.save()


admin.site.register(Article, ArticleAdmin)

