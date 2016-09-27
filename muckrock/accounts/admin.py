"""
Admin registration for accounts models
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist

from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin
import datetime
import stripe

from muckrock.accounts.models import Profile, Statistics, AgencyUser
from muckrock.jurisdiction.models import Jurisdiction

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods


class StatisticsAdmin(VersionAdmin):
    """Statistics admin options"""
    list_display = ('date', 'total_requests', 'total_requests_success', 'total_requests_denied',
                    'total_pages', 'total_users', 'total_agencies', 'total_fees')
    formats = ['xls', 'csv']


class ProfileAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    location = autocomplete_light.ModelChoiceField('JurisdictionAdminAutocomplete',
                                                   queryset=Jurisdiction.objects.all(),
                                                   required=False)

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Profile
        fields = '__all__'


class ProfileInline(admin.StackedInline):
    """Profile admin options"""
    model = Profile
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    form = ProfileAdminForm
    extra = 1
    max_num = 1


class MRUserAdmin(UserAdmin):
    """User admin options"""
    list_display = ('username', 'date_joined',)
    inlines = [ProfileInline]

    def save_related(self, request, form, formsets, change):
        """Creates/cancels a pro subscription if changing to/from pro acct_type"""
        obj = form.instance
        try:
            profile = obj.profile
            before_acct_type = profile.acct_type
        except ObjectDoesNotExist:
            profile = None
            before_acct_type = None
        try:
            after_acct_type = formsets[0].cleaned_data[0].get('acct_type')
        except IndexError:
            after_acct_type = None
        if change and profile:
            # we want to subscribe users when acct_type changes to 'pro'
            # and unsubscribe users when acct_type changes from 'pro'
            if before_acct_type != after_acct_type:
                try:
                    if after_acct_type == 'pro':
                        profile.start_pro_subscription()
                    elif before_acct_type == 'pro':
                        profile.cancel_pro_subscription()
                except (stripe.InvalidRequestError, stripe.CardError, ValueError) as exception:
                    messages.error(request, exception)
        else:
            # if creating a new pro from scratch, try starting their subscription
            try:
                if after_acct_type == 'pro':
                    profile.start_pro_subscription()
            except (stripe.InvalidRequestError, stripe.CardError, ValueError) as exception:
                messages.error(request, exception)
        obj.save()
        super(MRUserAdmin, self).save_related(request, form, formsets, change)


class AgencyProfileInline(ProfileInline):
    """Agency Profile admin inline options"""
    fields = (
            'phone',
            'fax',
            'salutation',
            'title',
            'address1',
            'address2',
            'city',
            'state',
            'zip_code',
            )


class AgencyUserAdmin(VersionAdmin):
    """Agency user admin"""
    list_display = ('username', 'first_name', 'last_name', 'email')
    fields = ('username', 'first_name', 'last_name', 'email')
    inlines = [AgencyProfileInline]

    def save_related(self, request, form, formsets, change):
        """Set account type on save"""
        super(AgencyUserAdmin, self).save_related(request, form, formsets, change)
        user = form.instance
        try:
            user.profile.acct_type = 'agency'
            user.profile.email_pref = 'never'
            user.profile.date_update = datetime.date.today()
            user.profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(
                    user=user,
                    acct_type='agency',
                    email_pref='never',
                    date_update=datetime.date.today(),
                    )


admin.site.register(Statistics, StatisticsAdmin)
admin.site.unregister(User)
admin.site.register(User, MRUserAdmin)
admin.site.register(AgencyUser, AgencyUserAdmin)
