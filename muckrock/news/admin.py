"""
Admin registration for news models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.core import autocomplete
from muckrock.news.models import Article, Photo


class AuthorListFilter(admin.SimpleListFilter):
    """Filter by authors"""

    title = "Author"
    parameter_name = "author"

    def lookups(self, request, model_admin):
        """All authors"""
        authors = (
            User.objects.exclude(authored_articles=None)
            .select_related("profile")
            .order_by("profile__full_name")
        )
        return tuple((a.pk, a.profile.full_name) for a in authors)

    def queryset(self, request, queryset):
        """Articles by the selected author"""
        if self.value():
            return queryset.filter(authors=self.value())


class ArticleAdminForm(forms.ModelForm):
    """Form with autocompletes"""

    authors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete", attrs={"data-placeholder": "User?"}
        ),
    )
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete", attrs={"data-placeholder": "User?"}
        ),
    )
    foias = autocomplete_light.ModelMultipleChoiceField(
        "FOIARequestAdminAutocomplete", required=False
    )

    class Meta:
        model = Article
        fields = "__all__"


class ArticleAdmin(VersionAdmin):
    """Model Admin for a news article"""

    # pylint: disable=too-many-public-methods
    form = ArticleAdminForm
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "get_authors_names", "pub_date", "publish")
    list_filter = ["pub_date", AuthorListFilter]
    date_hierarchy = "pub_date"
    search_fields = ["title", "body"]
    save_on_top = True

    def get_queryset(self, request):
        """Prefetch authors"""
        return (
            super(ArticleAdmin, self).get_queryset(request).prefetch_related("authors")
        )


admin.site.register(Article, ArticleAdmin)
admin.site.register(Photo)
