# Django
from django import forms
from django.contrib import admin, flatpages
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import render_flatpage
from django.shortcuts import get_object_or_404
from django.urls import re_path

# Third Party
from simple_history import register
from simple_history.admin import SimpleHistoryAdmin


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


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatpageAdmin)
register(FlatPage, app=__package__)
