# -*- coding: utf-8 -*-
"""Admin registration for communication models"""

# Django
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

# Third Party
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


class EmailAddressAdmin(VersionAdmin):
    """Email address admin"""

    search_fields = ["email", "name"]
    list_filter = ["status"]


class PhoneNumberAdmin(VersionAdmin):
    """Phone number admin"""

    search_fields = ["number"]
    list_display = ["__str__", "type"]
    list_filter = ["type", "status"]


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
                "description": "Override the entire address",
                "fields": ("address",),
            },
        ),
    )


class CheckAdmin(CommunicationLinkMixin, VersionAdmin):
    """Check admin"""

    search_fields = ["number"]
    list_display = [
        "number",
        "agency",
        "amount",
        "user",
        "created_datetime",
        "deposit_date",
    ]
    fields = [
        "number",
        "agency",
        "amount",
        "comm_link",
        "user",
        "created_datetime",
        "deposit_date",
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
