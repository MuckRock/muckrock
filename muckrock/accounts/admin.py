"""
Admin registration for accounts models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.safestring import mark_safe

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.accounts.models import Profile, RecurringDonation, Statistics
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
    fieldsets = (
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
    readonly_fields = ("username", "email")

    def full_name(self, obj):
        """Show full name from profile"""
        return obj.profile.full_name


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
        return super(RecurringDonationAdmin, self).save_model(
            request, obj, form, change
        )


admin.site.register(Statistics, StatisticsAdmin)
admin.site.unregister(User)
admin.site.register(User, MRUserAdmin)
admin.site.register(RecurringDonation, RecurringDonationAdmin)
