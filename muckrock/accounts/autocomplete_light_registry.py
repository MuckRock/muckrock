"""
Autocomplete registry for Accounts
"""

from django.contrib.auth.models import User

import autocomplete_light

class UserAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking users"""
    choices = User.objects.all()
    search_fields = ['^username', '^first_name', '^last_name', '^email']
    attrs = {
        'placeholder': 'Search users',
        'data-autocomplete-minimum-characters': 2
    }

class OrganizationAutocomplete(UserAutocomplete):
    """Adds organization-specific filtering for users"""
    def choices_for_request(self):
        # get filters
        query = self.request.GET.get('q', '')
        exclude = self.request.GET.getlist('exclude', '')
        org_id = self.request.GET.get('orgId', '')
        # get all choices
        choices = self.choices.all()
        # exclude choices based on filters
        if query:
            choices = choices.filter(username__icontains=query)
        for user_id in exclude:
            choices = choices.exclude(pk=int(user_id))
        if org_id: # exclude owner and members from choices
            organization = get_object_or_404(Organization, pk=org_id)
            owner = organization.owner
            profiles = organization.members.all()
            exclude_pks = [owner.pk] + [profile.user.pk for profile in profiles]
            choices = choices.exclude(pk__in=exclude_pks)
        # return final list of choices
        return self.order_choices(choices)[0:self.limit_choices]

autocomplete_light.register(User, UserAutocomplete)
autocomplete_light.register(User, OrganizationAutocomplete)
