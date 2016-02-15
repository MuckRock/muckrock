"""
Admin registration for news models
"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

from reversion import VersionAdmin
import autocomplete_light

from muckrock.news.models import Article, Photo


class AuthorListFilter(admin.SimpleListFilter):
    """Filter by authors"""
    title = 'Author'
    parameter_name = 'author'

    def lookups(self, request, model_admin):
        """All authors"""
        authors = User.objects.exclude(authored_articles=None)
        return tuple((a.pk, a.get_full_name()) for a in authors)

    def queryset(self, request, queryset):
        """Articles by the selected author"""
        if self.value():
            return queryset.filter(authors=self.value())


class ArticleAdminForm(forms.ModelForm):
    """Form with EpicEditor"""
    # pylint: disable=too-few-public-methods

    authors = forms.ModelMultipleChoiceField(
        queryset=User.objects.order_by('username'))
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.order_by('username'),
        required=False)
    foias = autocomplete_light.ModelMultipleChoiceField(
        'FOIARequestAdminAutocomplete',
        required=False)

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Article
        fields = '__all__'


class ArticleAdmin(VersionAdmin):
    """Model Admin for a news article"""
    # pylint: disable=too-many-public-methods
    form = ArticleAdminForm
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'get_authors_names', 'pub_date', 'publish')
    list_filter = ['pub_date', AuthorListFilter]
    date_hierarchy = 'pub_date'
    search_fields = ['title', 'body']
    save_on_top = True

admin.site.register(Article, ArticleAdmin)
admin.site.register(Photo)

