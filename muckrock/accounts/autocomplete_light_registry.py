"""
Autocomplete registry for Accounts
"""

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.accounts.models import AgencyUser
from muckrock.foia.models import FOIARequest
from muckrock.organization.models import Organization

class UserAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Creates an autocomplete field for picking users"""
    choices = User.objects.all()
    choice_template = 'autocomplete/user.html'
    search_fields = ['^username', '^first_name', '^last_name', '^email']
    attrs = {
        'placeholder': 'Search by name',
        'data-autocomplete-minimum-characters': 2
    }

    def choice_label(self, choice):
        """Uses the user's full name and username as the choice label."""
        label = choice.get_full_name() + ' (' + choice.username + ')'
        return label


class AgencyUserAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Agency user autocomplete"""
    choices = AgencyUser.objects.all()
    add_another_url_name = 'admin:accounts_agencyuser_add'
    search_fields = ['^username', '^first_name', '^last_name', '^email']
    attrs = {
        'placeholder': 'Search by name or email',
        'data-autocomplete-minimum-characters': 2
    }

    def choice_label(self, choice):
        """Uses the user's username and email as the choice label."""
        return '%s (%s)' % (choice.username, choice.email)


class UserEmailAutocomplete(autocomplete_light.AutocompleteModelBase):
    """User autocomplete for email situations"""
    choices = User.objects.all()
    search_fields = ['^username', '^first_name', '^last_name', '^email']
    attrs = {
        'placeholder': 'Search by name or email',
        'data-autocomplete-minimum-characters': 2
    }

    def choice_label(self, choice):
        """Uses the user's username and email as the choice label."""
        return '%s (%s)' % (choice.username, choice.email)


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
autocomplete_light.register(AgencyUser, AgencyUserAutocomplete)
autocomplete_light.register(User, UserEmailAutocomplete)
autocomplete_light.register(User, OrganizationAutocomplete)
autocomplete_light.register(User, RequestSharingAutocomplete)
