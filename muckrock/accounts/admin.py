"""
Admin registration for accounts models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
from django.http.response import HttpResponse
from django.urls import reverse
from django.urls.conf import re_path
from django.utils.safestring import mark_safe

# Standard Library
import csv

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.accounts.models import (
    Profile,
    RecurringDonation,
    Statistics,
    StockResponse,
)
from muckrock.agency.models import Agency
from muckrock.core import autocomplete
from muckrock.jurisdiction.models import Jurisdiction


class StatisticsAdmin(VersionAdmin):
    """Statistics admin options"""

    list_display = (
        "date",
        "total_requests",
        "total_requests_success",
        "total_requests_denied",
        "total_pages",
        "total_users",
        "total_agencies",
        "total_fees",
    )
    formats = ["xls", "csv"]
    autocomplete_fields = ["users_today"]

    def export_statistics_as_csv(self, request, queryset):
        """Export selected Statistics records to CSV."""

        excluded_fields = {
            "users_today",  # exclude the ManyToManyField
            "stale_agencies",
            "total_deferred_generic_tasks",
            "total_generic_tasks",
            "total_deferred_tasks",
            "total_deferred_snailmail_tasks",
            "total_deferred_orphan_tasks",
            "total_deferred_rejected_tasks",
            "total_staleagency_tasks",
            "total_unresolved_staleagency_tasks",
            "total_deferred_staleagency_tasks",
            "total_deferred_flagged_tasks",
            "total_deferred_newagency_tasks",
            "total_deferred_response_tasks",
            "total_deferred_faxfail_tasks",
            "total_deferred_payment_tasks",
            "total_crowdfundpayment_tasks",
            "total_unresolved_crowdfundpayment_tasks",
            "total_deferred_crowdfundpayment_tasks",
            "total_deferred_reviewagency_tasks",
            "total_deferred_portal_tasks",
        }

        field_names = [
            field.name
            for field in Statistics._meta.get_fields()
            if not field.auto_created and field.name not in excluded_fields
        ]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=statistics_export.csv"

        writer = csv.writer(response)
        writer.writerow(field_names)

        for obj in queryset:
            row = []
            for field_name in field_names:
                value = getattr(obj, field_name)
                if field_name == "date":
                    row.append(value.isoformat() if value else "")
                else:
                    row.append(value)
            writer.writerow(row)

        return response

    export_statistics_as_csv.short_description = "Export selected statistics to CSV"

    actions = [export_statistics_as_csv]


class ProfileAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    location = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Jurisdiction?", "data-width": None},
        ),
    )
    agency = forms.ModelChoiceField(
        queryset=Agency.objects.filter(status="approved"),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            attrs={"data-placeholder": "Agency?", "data-width": None},
        ),
    )

    class Meta:
        model = Profile
        fields = "__all__"


class ProfileInline(admin.StackedInline):
    """Profile admin options"""

    model = Profile
    search_fields = ("user__username", "full_name")
    form = ProfileAdminForm
    extra = 0
    max_num = 1
    fields = (
        "org_link",
        "uuid",
        "full_name",
        "email_confirmed",
        "email_pref",
        "source",
        "location",
        "avatar_url",
        "experimental",
        "use_autologin",
        "email_failed",
        "new_question_notifications",
        "org_share",
        "state",
        "proxy",
        "agency",
    )
    readonly_fields = ("org_link", "uuid", "full_name", "email_confirmed", "avatar_url")

    @mark_safe
    def org_link(self, obj):
        """Link to the individual org"""
        link = reverse(
            "admin:organization_organization_change",
            args=(obj.individual_organization.pk,),
        )
        return '<a href="%s">%s</a>' % (link, obj.individual_organization.name)

    org_link.short_description = "Individual Organization"


class MRUserAdmin(UserAdmin):
    """User admin options"""

    list_display = (
        "username",
        "date_joined",
        "email",
        "full_name",
        "is_staff",
        "is_superuser",
    )
    list_filter = UserAdmin.list_filter
    list_select_related = ("profile",)
    inlines = [ProfileInline]
    superuser_fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email",)}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    readonly_fields = ("username", "email")

    def get_fieldsets(self, request, obj=None):
        """Remove permission settings for non-super users"""
        if request.user.is_superuser:
            return self.superuser_fieldsets
        else:
            return self.fieldsets

    def full_name(self, obj):
        """Show full name from profile"""
        return obj.profile.full_name

    def get_urls(self):
        """Add custom URLs here"""
        urls = super().get_urls()
        my_urls = [
            re_path(
                r"^export/$",
                self.admin_site.admin_view(self.user_export),
                name="accounts-admin-user-export",
            ),
        ]
        return my_urls + urls

    def user_export(self, request):
        response = HttpResponse(
            content_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="muckrock_users.csv"'
            },
        )
        writer = csv.writer(response)

        def format_date(date):
            if date is not None:
                return date.strftime("%Y-%m-%d")
            else:
                return ""

        writer.writerow(
            ["username", "name", "email", "last_login", "date_joined", "requests"]
        )
        for user in (
            User.objects.filter(profile__agency=None)
            .select_related("profile")
            .only(
                "username", "profile__full_name", "email", "last_login", "date_joined"
            )
            .annotate(requests=Count("composers__foias"))
            .iterator(chunk_size=2000)
        ):
            writer.writerow(
                [
                    user.username,
                    user.profile.full_name,
                    user.email,
                    format_date(user.last_login),
                    format_date(user.date_joined),
                    user.requests,
                ]
            )

        return response


class RecurringDonationAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )

    class Meta:
        model = RecurringDonation
        fields = "__all__"


# this move to squarelet in the future


class RecurringDonationAdmin(VersionAdmin):
    """Recurring donation admin options"""

    model = RecurringDonation
    list_display = (
        "email",
        "user",
        "amount",
        "payment_failed",
        "active",
        "created_datetime",
    )
    list_select_related = ("user",)
    search_fields = ("email", "user__username")
    form = RecurringDonationAdminForm
    date_hierarchy = "created_datetime"
    list_filter = ("active", "payment_failed")
    readonly_fields = (
        "email",
        "created_datetime",
        "amount",
        "customer_id",
        "subscription_id",
        "deactivated_datetime",
    )

    def get_readonly_fields(self, request, obj=None):
        """Return read only fields"""
        if obj.active:
            return self.readonly_fields
        else:
            return self.readonly_fields + ("active",)

    def save_model(self, request, obj, form, change):
        """Cancel the subscription if manually deactivated"""
        if not obj.active:
            obj.cancel()
        return super().save_model(request, obj, form, change)


class StockResponseAdmin(VersionAdmin):
    model = StockResponse
    list_display = ("title", "type")
    list_filter = ("type",)


admin.site.register(Statistics, StatisticsAdmin)
admin.site.unregister(User)
admin.site.register(User, MRUserAdmin)
admin.site.register(RecurringDonation, RecurringDonationAdmin)
admin.site.register(StockResponse, StockResponseAdmin)
