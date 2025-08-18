# Django
from django import forms
from django.contrib import admin, flatpages
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import render_flatpage
from django.db.models import JSONField, TextField
from django.forms import widgets
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import re_path
from django.utils.encoding import force_str
from django.utils.translation import gettext as _

# Standard Library
import json

# Third Party
from reversion.admin import VersionAdmin
from simple_history import register
from simple_history.admin import SimpleHistoryAdmin

# MuckRock
from muckrock.core import autocomplete
from muckrock.core.models import FeaturedProjectSlot, HomePage
from muckrock.news.models import Article
from muckrock.project.models import Project


# https://stackoverflow.com/questions/48145992/showing-json-field-in-django-admin
# https://github.com/MuckRock/documentcloud/blob/master/documentcloud/addons/admin.py#L26-L38
class PrettyJSONWidget(widgets.Textarea):
    def format_value(self, value):
        try:
            # Accept Python objects and JSON strings
            if isinstance(value, (dict, list)):
                data = value
            elif value in (None, ""):
                return ""
            else:
                data = json.loads(value)

            pretty = json.dumps(data, indent=2, sort_keys=True)

            # these lines will try to adjust size of TextArea to fit to content
            row_lengths = [len(r) for r in pretty.split("\n")]
            self.attrs["rows"] = min(max(len(row_lengths) + 2, 10), 30)
            self.attrs["cols"] = min(max(max(row_lengths) + 2, 40), 120)
            return pretty
        except Exception:  # pylint: disable=broad-except
            return super().format_value(value)


class FlatpageForm(flatpages.admin.FlatpageForm):
    reason = forms.CharField(widget=forms.Textarea())


class FlatpageAdmin(SimpleHistoryAdmin, flatpages.admin.FlatPageAdmin):
    form = FlatpageForm
    fieldsets = (
        (None, {"fields": ("url", "title", "content", "reason", "sites")}),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": ("registration_required", "template_name"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        # pylint: disable=protected-access
        obj._change_reason = form.cleaned_data["reason"]
        return super().save_model(request, obj, form, change)

    def get_urls(self):
        """Add custom URLs here"""
        urls = super().get_urls()
        my_urls = [
            re_path(
                r"^preview/(?P<idx>\d+)/$",
                self.admin_site.admin_view(self.preview),
                name="flatpage-preview",
            ),
        ]
        return my_urls + urls

    def preview(self, request, idx):
        """Preview the flatpage"""
        flatpage = get_object_or_404(FlatPage, pk=idx)
        flatpage.content = request.POST.get("content")
        return render_flatpage(request, flatpage)


class SingletonModelAdmin(VersionAdmin):
    """
    Admin class for singleton models with version control.
    """

    singleton_instance_id = 1

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        """
        Overridden default get_urls to directly display
        change form instead of List Display
        """
        urls = super().get_urls()
        model_name = self.model._meta.model_name

        url_name_prefix = "%(app_name)s_%(model_name)s" % {
            "app_name": self.model._meta.app_label,
            "model_name": model_name,
        }
        custom_urls = [
            re_path(
                r"^history/$",
                self.admin_site.admin_view(self.history_view),
                {"object_id": str(self.singleton_instance_id)},
                name="%s_history" % url_name_prefix,
            ),
            re_path(
                r"^$",
                self.admin_site.admin_view(self.change_view),
                {"object_id": str(self.singleton_instance_id)},
                name="%s_change" % url_name_prefix,
            ),
        ]

        return custom_urls + urls

    def response_change(self, request, obj):
        """
        Overridden default response_change to redirect
        to home page instead of list display page
        """
        msg = _("%(obj)s was changed successfully.") % {"obj": force_str(obj)}
        if "_continue" in request.POST:
            self.message_user(request, msg + " " + _("You may edit it again below."))
            return HttpResponseRedirect(request.path)
        else:
            self.message_user(request, msg)
            return HttpResponseRedirect("../../")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """
        Overridden default change_view to display change
        form for the default singleton instance id
        """
        if object_id == str(self.singleton_instance_id):
            self.model.objects.get_or_create(pk=self.singleton_instance_id)

        if not extra_context:
            extra_context = {}
        extra_context["skip_object_list_page"] = True

        return super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )

    def history_view(self, request, object_id, extra_context=None):
        """
        Overridden default change_view to display
        history of the default singleton instance id
        """
        if not extra_context:
            extra_context = {}
        extra_context["skip_object_list_page"] = True

        return super().history_view(
            request,
            object_id,
            extra_context=extra_context,
        )


class FeaturedProjectSlotForm(forms.ModelForm):

    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=True,
        widget=autocomplete.ModelSelect2(
            url="project-autocomplete",
            attrs={"data-placeholder": "Select a project", "data-width": None},
        ),
    )

    articles = forms.ModelMultipleChoiceField(
        queryset=Article.objects.get_published(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="article-autocomplete",
            forward=("project",),
            attrs={"data-placeholder": "Select articles", "data-width": None},
        ),
    )

    class Meta:
        model = FeaturedProjectSlot
        fields = ("order", "project", "articles")


class FeaturedProjectSlotInline(admin.TabularInline):
    model = FeaturedProjectSlot
    form = FeaturedProjectSlotForm
    extra = 1
    fields = ("order", "project", "articles")
    ordering = ("order",)


@admin.register(HomePage)
class HomePageAdmin(SingletonModelAdmin):
    inlines = [FeaturedProjectSlotInline]
    fields = (
        "about_heading",
        "about_paragraph",
        "documentcloud_stats",
        "dlp_stats",
        "expertise_sections",
    )
    formfield_overrides = {
        TextField: {"widget": admin.widgets.AdminTextareaWidget},
        JSONField: {"widget": PrettyJSONWidget},
    }

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r"^get-articles-for-project/$",
                self.admin_site.admin_view(self.get_articles_for_project),
                name="get_articles_for_project",
            ),
        ]
        return custom_urls + urls

    def get_articles_for_project(self, request):
        project_id = request.GET.get("project_id")
        articles = []
        if project_id:
            qs = Article.objects.filter(projects__id=project_id)
            articles = [{"id": a.id, "title": a.title} for a in qs]
        return JsonResponse({"articles": articles})


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatpageAdmin)
register(FlatPage, app=__package__)
