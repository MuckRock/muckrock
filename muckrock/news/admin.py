"""
Admin registration for news models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.core import autocomplete
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article, Authorship, Photo


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
        else:
            return None


class AuthorshipAdminForm(forms.ModelForm):
    """Admin form for Authorship"""

    author = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )

    class Meta:
        model = Authorship
        fields = "__all__"


class AuthorInline(admin.TabularInline):
    """Authorship Admin Inline"""

    model = Authorship
    form = AuthorshipAdminForm
    extra = 1
    fields = ["author", "order"]


class ArticleAdminForm(forms.ModelForm):
    """Form with autocompletes"""

    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )
    foias = forms.ModelMultipleChoiceField(
        queryset=FOIARequest.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="foia-request-autocomplete",
            attrs={"data-placeholder": "FOIA?", "data-width": None},
        ),
    )

    class Meta:
        model = Article
        fields = [
            "pub_date",
            "title",
            "kicker",
            "slug",
            "summary",
            "body",
            "editors",
            "publish",
            "foias",
            "image",
            "tags",
        ]


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
    inlines = [AuthorInline]

    def get_queryset(self, request):
        """Prefetch authors"""
        return (
            super(ArticleAdmin, self).get_queryset(request).prefetch_related("authors")
        )


admin.site.register(Article, ArticleAdmin)
admin.site.register(Photo)
