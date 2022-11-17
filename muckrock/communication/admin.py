# -*- coding: utf-8 -*-
"""Admin registration for communication models"""

# Django
from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

# Third Party
from localflavor.us.forms import USZipCodeField
from localflavor.us.us_states import STATE_CHOICES
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.communication.models import (
    Address,
    Check,
    EmailAddress,
    EmailCommunication,
    EmailError,
    EmailOpen,
    FaxCommunication,
    FaxError,
    MailCommunication,
    MailEvent,
    PhoneNumber,
    PortalCommunication,
    Source,
    WebCommunication,
)


class ReadOnlyMixin:
    """Admin mixin to make all fields read-only"""

    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly"""
        # pylint: disable=unused-argument
        return [field.name for field in self.opts.local_fields] + [
            field.name for field in self.opts.local_many_to_many
        ]


class CommunicationLinkMixin:
    """Admin mixin to show FOIA Communication link"""

    @mark_safe
    def comm_link(self, obj):
        """Link to the FOIA communication admin"""
        link = reverse(
            "admin:foia_foiacommunication_change", args=(obj.communication.pk,)
        )
        return '<a href="%s">FOIA Communication</a>' % link

    comm_link.short_description = "FOIA Communication"


class EmailErrorInline(ReadOnlyMixin, admin.StackedInline):
    """Email Error Inline admin options"""

    model = EmailError
    extra = 0


class EmailOpenInline(ReadOnlyMixin, admin.StackedInline):
    """Email Open Inline admin options"""

    model = EmailOpen
    extra = 0


class MailEventInline(ReadOnlyMixin, admin.StackedInline):
    """Mail Event Inline admin options"""

    model = MailEvent
    extra = 0


class FaxErrorInline(ReadOnlyMixin, admin.StackedInline):
    """Fax Error Inline admin options"""

    model = FaxError
    extra = 0


class EmailCommunicationAdmin(CommunicationLinkMixin, VersionAdmin):
    """Email Communication admin"""

    model = EmailCommunication
    inlines = [EmailOpenInline, EmailErrorInline]

    fields = (
        "comm_link",
        "sent_datetime",
        "confirmed_datetime",
        "from_email",
        "to_emails",
        "cc_emails",
    )
    readonly_fields = fields


class EmailCommunicationInline(admin.StackedInline):
    """Email Communication Inline admin"""

    model = EmailCommunication
    show_change_link = True
    extra = 0
    fields = (
        "sent_datetime",
        "confirmed_datetime",
        "from_email",
        "to_emails",
        "cc_emails",
        "open",
        "error",
    )
    readonly_fields = fields

    def open(self, instance):
        """Does this email have an open?"""
        return instance.opens.count() > 0

    open.boolean = True

    def error(self, instance):
        """Does this email have an error?"""
        return instance.errors.count() > 0

    error.boolean = True


class FaxCommunicationAdmin(CommunicationLinkMixin, VersionAdmin):
    """Fax Communication admin"""

    model = FaxCommunication
    inlines = [FaxErrorInline]

    fields = ("comm_link", "sent_datetime", "confirmed_datetime", "to_number", "fax_id")
    readonly_fields = fields


class FaxCommunicationInline(admin.StackedInline):
    """Fax Communication Inline admin"""

    model = FaxCommunication
    show_change_link = True
    extra = 0
    fields = ("sent_datetime", "confirmed_datetime", "to_number", "fax_id", "error")
    readonly_fields = fields

    def error(self, instance):
        """Does this fax have an error?"""
        return instance.errors.count() > 0

    error.boolean = True


class MailCommunicationAdmin(CommunicationLinkMixin, ReadOnlyMixin, VersionAdmin):
    """Mail Communication admin"""

    model = MailCommunication
    inlines = [MailEventInline]


class MailCommunicationInline(ReadOnlyMixin, admin.StackedInline):
    """Mail Communication Inline admin"""

    model = MailCommunication
    show_change_link = True
    extra = 0


class WebCommunicationInline(ReadOnlyMixin, admin.StackedInline):
    """Mail Communication Inline admin"""

    model = WebCommunication
    extra = 0


class PortalCommunicationInline(ReadOnlyMixin, admin.StackedInline):
    """Portal Communication Inline admin"""

    model = PortalCommunication
    extra = 0


class SourceInline(admin.StackedInline):
    """Source Inline admin"""

    model = Source
    fields = ["datetime", "user", "type", "url"]
    autocomplete_fields = ["user"]
    extra = 1


class EmailAddressAdmin(VersionAdmin):
    """Email address admin"""

    search_fields = ["email", "name"]
    list_filter = ["status"]
    fields = ["email", "name", "status"]
    inlines = [SourceInline]


class PhoneNumberAdmin(VersionAdmin):
    """Phone number admin"""

    search_fields = ["number"]
    list_display = ["__str__", "type"]
    list_filter = ["type", "status"]
    inlines = [SourceInline]


class AddressAdminForm(forms.ModelForm):
    # Character limits are for conforming to Lob's requirements
    agency_override = forms.CharField(
        max_length=40,
        label="Name",
        required=False,
        help_text="Who the letter should be addressed to.  If left blank, will default "
        "to the agency's name.",
    )
    attn_override = forms.CharField(
        max_length=34,
        label="Attention of",
        required=False,
        help_text="Who the letter should be to the attention of.  If left blank, "
        "will default to the FOIA Office (or applicable law for states).",
    )
    street = forms.CharField(max_length=64)
    suite = forms.CharField(max_length=64, required=False)
    city = forms.CharField(max_length=200)
    state = forms.ChoiceField(choices=(("", "---"),) + tuple(STATE_CHOICES))
    zip_code = USZipCodeField()

    class Meta:
        model = Address
        fields = [
            "agency_override",
            "attn_override",
            "street",
            "suite",
            "city",
            "state",
            "zip_code",
        ]


class AddressAdmin(VersionAdmin):
    """Address admin"""

    search_fields = [
        "address",
        "street",
        "suite",
        "city",
        "state",
        "zip_code",
        "agency_override",
        "attn_override",
    ]
    readonly_fields = ["address"]
    form = AddressAdminForm
    fieldsets = (
        (None, {"fields": ("street", "suite", "city", "state", "zip_code")}),
        (
            "Override Fields",
            {
                "classes": ("collapse",),
                "description": "Override particular fields",
                "fields": ("agency_override", "attn_override"),
            },
        ),
        (
            "Full override",
            {
                "classes": ("collapse",),
                "description": "Override the entire address.  This field is "
                "deprecated, as it is not compatible with Lob.  The address must "
                "be made to fit the fields above in order to automatically mail "
                "letters via Lob.",
                "fields": ("address",),
            },
        ),
    )
    inlines = [SourceInline]


class CheckAdmin(CommunicationLinkMixin, VersionAdmin):
    """Check admin"""

    search_fields = ["number"]
    list_display = [
        "number",
        "agency",
        "amount",
        "user",
        "created_datetime",
        "status_date",
        "status",
    ]
    list_filter = ["status"]
    fields = [
        "number",
        "agency",
        "amount",
        "comm_link",
        "user",
        "created_datetime",
        "status_date",
        "status",
    ]
    readonly_fields = [
        "number",
        "agency",
        "amount",
        "comm_link",
        "user",
        "created_datetime",
    ]


admin.site.register(EmailCommunication, EmailCommunicationAdmin)
admin.site.register(FaxCommunication, FaxCommunicationAdmin)
admin.site.register(MailCommunication, MailCommunicationAdmin)
admin.site.register(EmailAddress, EmailAddressAdmin)
admin.site.register(PhoneNumber, PhoneNumberAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Check, CheckAdmin)
