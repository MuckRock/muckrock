"""
Admin registration for organization models
"""

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.models import User

import autocomplete_light
from reversion import VersionAdmin
import stripe

from muckrock.organization.models import Organization


class OrganizationAdminForm(forms.ModelForm):
    """Agency admin form to order users"""
    owner = autocomplete_light.ModelChoiceField(
        'UserAutocomplete',
        queryset=User.objects.all(),
        required=False
    )

    def clean_owner(self):
        """Ensures name is unique"""
        owner = self.cleaned_data['owner']
        if not owner:
            raise forms.ValidationError('Organization must have an owner.')
        return owner

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Organization
        fields = '__all__'


class OrganizationAdmin(VersionAdmin):
    """Organization Admin"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner')
    form = OrganizationAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.stripe_id:
            obj.create_plan()
            obj.owner.profile.customer()
        if change:
            original = Organization.objects.get(pk=obj.pk)
            if original.monthly_cost != obj.monthly_cost:
                try:
                    obj.update_plan()
                except (stripe.InvalidRequestError, stripe.CardError, ValueError) as exception:
                    messages.error(request, exception)
                    return
        obj.save()

admin.site.register(Organization, OrganizationAdmin)

