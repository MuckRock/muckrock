"""
Admin registration for organization models
"""

# Django
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.safestring import mark_safe

# Third Party
import reversion
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.organization.models import Entitlement, Organization


class OrganizationAdminForm(forms.ModelForm):
    """Adjust purchased requests by an amount instead of setting them"""

    number_requests_change = forms.IntegerField(
        label="Change number requests by",
        initial=0,
        required=False,
        min_value=-settings.MAX_REQUESTS_CHANGE,
        max_value=settings.MAX_REQUESTS_CHANGE,
        help_text=(
            "Added to Number requests above. Use a negative number to remove "
            f"(max {settings.MAX_REQUESTS_CHANGE} at a time)"
        ),
    )

    class Meta:
        model = Organization
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        number_change = cleaned_data.get("number_requests_change") or 0
        if self.instance.number_requests + number_change < 0:
            raise forms.ValidationError(
                "Number requests cannot go below 0 "
                f"(currently {self.instance.number_requests})"
            )
        return cleaned_data


class OrganizationAdmin(VersionAdmin):
    """Organization Admin"""

    form = OrganizationAdminForm
    list_display = ("name", "entitlement", "private", "individual")
    list_filter = ("entitlement", "private", "individual")
    search_fields = ("name", "users__username")
    fields = (
        "uuid",
        "name",
        "slug",
        "private",
        "individual",
        "entitlement",
        "card",
        "requests_per_month",
        "monthly_requests",
        "number_requests",
        "number_requests_change",
        "date_update",
        "verified_journalist",
    )
    readonly_fields = (
        "uuid",
        "name",
        "slug",
        "private",
        "individual",
        "entitlement",
        "card",
        "requests_per_month",
        "monthly_requests",
        "number_requests",
        "date_update",
        "verified_journalist",
    )

    def get_fields(self, request, obj=None):
        """Only add user link for individual organizations"""
        if obj and obj.individual:
            return ("user_link",) + self.fields
        else:
            return self.fields

    def get_readonly_fields(self, request, obj=None):
        """Only add user link for individual organizations"""
        if obj and obj.individual:
            return ("user_link",) + self.readonly_fields
        else:
            return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """Apply purchased request changes as a delta so we can't clobber"""
        if not change:
            super().save_model(request, obj, form, change)
            return
        number_change = form.cleaned_data.get("number_requests_change") or 0
        if number_change == 0:
            return
        obj.add_requests(number_change)
        # replace the F() snapshot from add_requests with the real balance
        obj.refresh_from_db(fields=["number_requests"])
        reversion.add_to_revision(obj)

    @mark_safe
    def user_link(self, obj):
        """Link to the individual org's user"""
        user = User.objects.get(profile__uuid=obj.uuid)
        link = reverse("admin:auth_user_change", args=(user.pk,))
        return '<a href="%s">%s</a>' % (link, user.username)

    user_link.short_description = "User"


class EntitlementAdmin(VersionAdmin):
    """Entitlement Admin"""

    list_display = (
        "name",
        "minimum_users",
        "base_requests",
        "requests_per_user",
        "feature_level",
    )


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Entitlement, EntitlementAdmin)
