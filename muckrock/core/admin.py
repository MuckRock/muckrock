# Django
from django import forms
from django.contrib import admin, flatpages
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import render_flatpage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import re_path
from django.utils.encoding import force_str
from django.utils.translation import gettext as _

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
        Overridden default get_urls to directly display change form instead of List Display
        """
        urls = super(SingletonModelAdmin, self).get_urls()
        model_name = self.model._meta.model_name

        url_name_prefix = '%(app_name)s_%(model_name)s' % {
            'app_name': self.model._meta.app_label,
            'model_name': model_name,
        }
        custom_urls = [
            re_path(r'^history/$',
                    self.admin_site.admin_view(self.history_view),
                    {'object_id': str(self.singleton_instance_id)},
                    name='%s_history' % url_name_prefix),
            re_path(r'^$',
                    self.admin_site.admin_view(self.change_view),
                    {'object_id': str(self.singleton_instance_id)},
                    name='%s_change' % url_name_prefix),
        ]

        return custom_urls + urls
    
    def response_change(self, request, obj):
        """
        Overridden default response_change to redirect to home page instead of list display page
        """
        msg = _('%(obj)s was changed successfully.') % {
            'obj': force_str(obj)}
        if '_continue' in request.POST:
            self.message_user(request, msg + ' ' +
                              _('You may edit it again below.'))
            return HttpResponseRedirect(request.path)
        else:
            self.message_user(request, msg)
            return HttpResponseRedirect("../../")

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
         Overridden default change_view to display change form for the default singleton instance id
        """
        if object_id == str(self.singleton_instance_id):
            self.model.objects.get_or_create(pk=self.singleton_instance_id)

        if not extra_context:
            extra_context = dict()
        extra_context['skip_object_list_page'] = True

        return super(SingletonModelAdmin, self).change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )

    def history_view(self, request, object_id, extra_context=None):
        """
        Overridden default change_view to display hostory of the default singleton instance id
        """
        if not extra_context:
            extra_context = dict()
        extra_context['skip_object_list_page'] = True

        return super(SingletonModelAdmin, self).history_view(
            request,
            object_id,
            extra_context=extra_context,
        )

    @property
    def singleton_instance_id(self):
        return getattr(self.model, 'singleton_instance_id', self.singleton_instance_id)


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatpageAdmin)
register(FlatPage, app=__package__)
