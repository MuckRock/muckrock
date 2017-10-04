# -*- coding: utf-8 -*-
"""Admin registration for communication models"""

from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse

from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

from muckrock.communication.models import (
        Address,
        EmailAddress,
        PhoneNumber,
        EmailCommunication,
        FaxCommunication,
        MailCommunication,
        WebCommunication,
        EmailOpen,
        EmailError,
        FaxError,
        )


class ReadOnlyMixin(object):
    """Admin mixin to make all fields read-only"""

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly"""
        # pylint: disable=unused-argument

        return [field.name for field in self.opts.local_fields]


class CommunicationLinkMixin(object):
    """Admin mixin to show FOIA Communication link"""
    def comm_link(self, obj):
        """Link to the FOIA communication admin"""
        # pylint: disable=no-self-use
        link = reverse(
                'admin:foia_foiacommunication_change',
                args=(obj.communication.pk,),
                )
        return '<a href="%s">FOIA Communication</a>' % link
    comm_link.allow_tags = True
    comm_link.short_description = 'FOIA Communication'


class EmailErrorInline(ReadOnlyMixin, admin.StackedInline):
    """Email Error Inline admin options"""
    model = EmailError
    extra = 0


class EmailOpenInline(ReadOnlyMixin, admin.StackedInline):
    """Email Open Inline admin options"""
    model = EmailOpen
    extra = 0


class FaxErrorInline(ReadOnlyMixin, admin.StackedInline):
    """Fax Error Inline admin options"""
    model = FaxError
    extra = 0


class EmailCommunicationAdminForm(forms.ModelForm):
    """Email Communication Inline admin form"""
    from_email = autocomplete_light.ModelChoiceField(
            'EmailAddressAutocomplete',
            queryset=EmailAddress.objects.all(),
            required=False,
            )
    to_emails = autocomplete_light.ModelMultipleChoiceField(
            'EmailAddressAutocomplete',
            queryset=EmailAddress.objects.all(),
            required=False,
            )
    cc_emails = autocomplete_light.ModelMultipleChoiceField(
            'EmailAddressAutocomplete',
            queryset=EmailAddress.objects.all(),
            required=False,
            )

    class Meta:
        model = EmailCommunication
        fields = '__all__'


class EmailCommunicationAdmin(CommunicationLinkMixin, VersionAdmin):
    """Email Communication admin"""
    model = EmailCommunication
    form = EmailCommunicationAdminForm
    inlines = [EmailOpenInline, EmailErrorInline]

    readonly_fields = ('comm_link',)
    fields = (
            'comm_link',
            'sent_datetime',
            'confirmed_datetime',
            'from_email',
            'to_emails',
            'cc_emails',
            )


class EmailCommunicationInline(admin.StackedInline):
    """Email Communication Inline admin"""
    model = EmailCommunication
    form = EmailCommunicationAdminForm
    show_change_link = True
    extra = 0


class FaxCommunicationAdminForm(forms.ModelForm):
    """Fax Communication Inline admin form"""
    to_number = autocomplete_light.ModelChoiceField(
            'PhoneNumberFaxAutocomplete',
            queryset=PhoneNumber.objects.filter(type='fax'),
            required=False,
            )

    class Meta:
        model = FaxCommunication
        fields = '__all__'


class FaxCommunicationAdmin(CommunicationLinkMixin, VersionAdmin):
    """Fax Communication admin"""
    model = FaxCommunication
    form = FaxCommunicationAdminForm
    inlines = [FaxErrorInline]

    readonly_fields = ('comm_link',)
    fields = (
            'comm_link',
            'sent_datetime',
            'confirmed_datetime',
            'to_number',
            'fax_id',
            )


class FaxCommunicationInline(admin.StackedInline):
    """Fax Communication Inline admin"""
    model = FaxCommunication
    form = FaxCommunicationAdminForm
    show_change_link = True
    extra = 0


class MailCommunicationAdminForm(forms.ModelForm):
    """Mail Communication Inline admin form"""
    from_address = autocomplete_light.ModelChoiceField(
            'AddressAutocomplete',
            queryset=Address.objects.all(),
            required=False,
            )
    to_address = autocomplete_light.ModelChoiceField(
            'AddressAutocomplete',
            queryset=Address.objects.all(),
            required=False,
            )

    class Meta:
        model = MailCommunication
        fields = '__all__'


class MailCommunicationInline(admin.StackedInline):
    """Mail Communication Inline admin"""
    model = MailCommunication
    form = MailCommunicationAdminForm
    extra = 0


class WebCommunicationInline(admin.StackedInline):
    """Mail Communication Inline admin"""
    model = WebCommunication
    extra = 0


class EmailAddressAdmin(VersionAdmin):
    """Email address admin"""
    search_fields = ['email', 'name']


class PhoneNumberAdmin(VersionAdmin):
    """Phone number admin"""
    search_fields = ['number']
    list_display = ['__unicode__', 'type']
    list_filter = ['type']


class AddressAdmin(VersionAdmin):
    """Address admin"""
    search_fields = ['address']
    fields = ['address']


admin.site.register(EmailCommunication, EmailCommunicationAdmin)
admin.site.register(FaxCommunication, FaxCommunicationAdmin)
admin.site.register(EmailAddress, EmailAddressAdmin)
admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(Address, AddressAdmin)
