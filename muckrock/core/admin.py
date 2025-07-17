# Django
from django import forms
from django.contrib import admin, flatpages
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import render_flatpage
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import re_path
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.db.models import TextField

# Third Party
from simple_history import register
from simple_history.admin import SimpleHistoryAdmin

# Local
from muckrock.core.models import HomePage, FeaturedProjectSlot
from muckrock.news.models import Article


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


class SingletonModelAdmin(admin.ModelAdmin):
    """
    Admin class for singleton models.
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

    # pylint: disable=function-redefined
    @property
    def singleton_instance_id(self):
        return getattr(
            self.model, "singleton_instance_id", type(self).singleton_instance_id
        )


class FeaturedProjectSlotInline(admin.TabularInline):
    model = FeaturedProjectSlot
    extra = 1
    fields = ("order", "project", "articles")
    ordering = ("order",)

    class Media:
        js = ("js/admin-featured-project-slot.js",)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        original_init = formset.__init__

        def formset_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            for form in self.forms:
                instance = getattr(form, "instance", None)
                if instance and instance.pk and instance.project_id:
                    form.fields["articles"].queryset = Article.objects.filter(
                        projects__id=instance.project_id
                    )
                # For new objects, get project from POST data
                elif request.method == "POST":
                    prefix = form.prefix  # e.g. featuredprojectslot_set-0
                    project_field = f"{prefix}-project"
                    project_id = request.POST.get(project_field)
                    if project_id:
                        form.fields["articles"].queryset = Article.objects.filter(
                            projects__id=project_id
                        )
                    else:
                        form.fields["articles"].queryset = Article.objects.none()
                else:
                    form.fields["articles"].queryset = Article.objects.none()

        formset.__init__ = formset_init
        return formset

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "articles":
            project_id = None
            if request is not None:
                data = request.POST or request.GET
                for key, value in data.items():
                    if key.endswith("-project") and value:
                        project_id = value
                        break
            if project_id:
                kwargs["queryset"] = Article.objects.filter(projects__id=project_id)
            else:
                kwargs["queryset"] = Article.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(HomePage)
class HomePageAdmin(SingletonModelAdmin):
    inlines = [FeaturedProjectSlotInline]
    fields = ("about_heading", "about_paragraph", "product_stats", "expertise_sections")
    formfield_overrides = {TextField: {"widget": admin.widgets.AdminTextareaWidget}}

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
