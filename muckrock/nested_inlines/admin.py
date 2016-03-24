
"""
Nested Inlines
"""
# pylint: disable-all

from django.contrib.admin import ModelAdmin, helpers
from django.contrib.admin.options import InlineModelAdmin
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.forms.formsets import all_valid
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.encoding import force_unicode
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect

csrf_protect_m = method_decorator(csrf_protect)

class NestedModelAdmin(ModelAdmin):
    """A model admin that can have nested inlines"""

    def _nested_formsets(self, request, admin, instance, create_formset, prefixes=None,
                         qs_field=None):
        """Collect all formsets recursively"""
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-locals

        formsets = []
        inline_admin_formsets = []
        media = []
        prefixes = prefixes or {}
        if not hasattr(admin, 'inline_instances'):
            admin.inline_instances = admin.get_inline_instances(request)
        for form_set, inline in admin.get_formsets_with_inlines(request):
            prefix = form_set.get_default_prefix()
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if prefixes[prefix] != 1:
                prefix = "%s-%s" % (prefix, prefixes[prefix])

            new_qs_field = None
            if qs_field:
                # if we were passed a qs_field, grab the qs from their directly to avoid
                # hitting the database again
                qset = getattr(instance, qs_field).all()
            elif hasattr(inline, 'prefetch'):
                # we prefetch the related field, then pass that field recursively
                qset = inline.get_queryset(request).prefetch_related(inline.prefetch)
                new_qs_field = inline.prefetch
            else:
                # normal qs
                qset = inline.get_queryset(request)
            formset = create_formset(form_set, request, admin, instance, prefix, qset)
            formsets.append(formset)

            fieldsets = list(inline.get_fieldsets(request))
            readonly = list(inline.get_readonly_fields(request))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, readonly_fields=readonly, model_admin=admin)
            inline_admin_formsets.append(inline_admin_formset)
            media.append(inline_admin_formset.media)

            for form in formset.forms:
                new_formsets, new_inline_admin_formsets, new_media = \
                    self._nested_formsets(request, inline, form.instance,
                                          create_formset, prefixes=prefixes, qs_field=new_qs_field)
                formsets.extend(new_formsets)
                form.inline_admin_formsets = new_inline_admin_formsets
                media.extend(new_media)

        return formsets, inline_admin_formsets, media


    @csrf_protect_m
    @transaction.atomic
    def add_view(self, request, form_url='', extra_context=None):
        """The 'add' admin view for this model."""
        # pylint: disable=protected-access
        model = self.model
        opts = model._meta

        if not self.has_add_permission(request):
            raise PermissionDenied

        ModelForm = self.get_form(request)
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES)
            if form.is_valid():
                new_object = self.save_form(request, form, change=False)
                form_validated = True
            else:
                form_validated = False
                new_object = self.model()

            formsets, inline_admin_formsets, media = \
                self._nested_formsets(request, self, new_object,
                    lambda FormSet, req, admin, inst, prefix, queryset:
                        FormSet(data=req.POST, files=req.FILES, instance=inst,
                                save_as_new=req.POST.has_key('_saveasnew'),
                                prefix=prefix, queryset=queryset))

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=False)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=False)

                self.log_addition(request, new_object)
                return self.response_add(request, new_object)
        else:
            # Prepare the dict of initial data from the request.
            # We have to special-case M2Ms as a list of comma-separated PKs.
            initial = dict(request.GET.items())
            for k in initial:
                try:
                    f = opts.get_field(k)
                except models.FieldDoesNotExist:
                    continue
                if isinstance(f, models.ManyToManyField):
                    initial[k] = initial[k].split(",")
            form = ModelForm(initial=initial)

            formsets, inline_admin_formsets, media = \
                self._nested_formsets(request, self, None,
                    lambda FormSet, req, admin, inst, prefix, queryset:
                        FormSet(instance=admin.model(), prefix=prefix,
                                queryset=queryset))

        adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
            self.prepopulated_fields, self.get_readonly_fields(request),
            model_admin=self)

        new_media = self.media + adminForm.media
        for m in media:
            new_media = new_media + m
        media = new_media

        context = {
            'title': _('Add %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'is_popup': request.REQUEST.has_key('_popup'),
            'show_delete': False,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
            'level': 1,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, form_url=form_url, add=True)


    @csrf_protect_m
    @transaction.atomic
    def change_view(self, request, object_id, extra_context=None):
        "The 'change' admin view for this model."
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') %
                {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and request.POST.has_key("_saveasnew"):
            return self.add_view(request, form_url='../add/')

        ModelForm = self.get_form(request, obj)
        formsets = []
        if request.method == 'POST':
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj

            formsets, inline_admin_formsets, media = \
                self._nested_formsets(request, self, new_object,
                    lambda FormSet, req, admin, inst, prefix, qs:
                        FormSet(data=req.POST, files=req.FILES, instance=inst,
                                prefix=prefix, queryset=qs))

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                form.save_m2m()
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)

                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = ModelForm(instance=obj)
            formsets, inline_admin_formsets, media = \
                self._nested_formsets(request, self, obj,
                    lambda FormSet, req, admin, inst, prefix, qs:
                        FormSet(instance=inst, prefix=prefix, queryset=qs))

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
            self.prepopulated_fields, self.get_readonly_fields(request, obj),
            model_admin=self)

        new_media = self.media + adminForm.media
        for m in media:
            new_media = new_media + m
        media = new_media

        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': request.REQUEST.has_key('_popup'),
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
            'level': 1,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)


class NestedInlineModelAdmin(InlineModelAdmin):
    """An inline model admin that can be nested"""

    inlines = []

    def __init__(self, parent_model, admin_site):
        super(NestedInlineModelAdmin, self).__init__(parent_model, admin_site)
        self.inline_instances = []
        for inline_class in self.inlines:
            inline_instance = inline_class(self.model, self.admin_site)
            self.inline_instances.append(inline_instance)

    def get_formsets_with_inlines(self, request, obj=None):
        """Get formsets and inlines for inlines"""
        for inline in self.inline_instances:
            yield inline.get_formsets_with_inlines(request, obj)


# would put this in for a patch, not sure if worth monkey patching in


class NestedStackedInline(NestedInlineModelAdmin):
    """Nested inline with stacked template"""
    template = 'admin/nested_inlines/stacked.html'

class NestedTabularInline(NestedInlineModelAdmin):
    """Nested inline with tabular template"""
    template = 'admin/nested_inlines/tabular.html'

# validate_inline should call itself recursively - don't feel like monkey patching
