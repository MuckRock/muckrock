"""
Autocomplete registry for Accounts
"""

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

import autocomplete_light

from muckrock.foia.models import FOIARequest
from muckrock.organization.models import Organization

class UserAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking users"""
    choices = User.objects.all()
    search_fields = ['^username', '^first_name', '^last_name', '^email']
    attrs = {
        'placeholder': 'Search users',
        'data-autocomplete-minimum-characters': 2
    }

    def choice_label(self, choice):
        """Uses the user's full name as the choice label."""
        return choice.get_full_name()

class RequestSharingAutocomplete(UserAutocomplete):
    """Adds request sharing filtering for users"""
    def choices_for_request(self):
        # get filters
        query = self.request.GET.get('q', '')
        foia_id = self.request.GET.get('foiaId', '')
        # get all choices
        choices = self.choices
        conditions = self._choices_for_request_conditions(query, self.search_fields)
        choices = choices.filter(conditions)
        if foia_id:
            foia = get_object_or_404(FOIARequest, pk=foia_id)
            creator = foia.user
            editors = foia.edit_collaborators.all()
            viewers = foia.read_collaborators.all()
            exclude_pks = [creator.pk]
            exclude_pks += [editor.pk for editor in editors]
            exclude_pks += [viewer.pk for viewer in viewers]
            choices = choices.exclude(pk__in=exclude_pks)
        # return final list of choices
        return self.order_choices(choices)[0:self.limit_choices]

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
autocomplete_light.register(User, RequestSharingAutocomplete)
