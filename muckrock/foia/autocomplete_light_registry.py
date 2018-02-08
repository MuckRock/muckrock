"""
Autocomplete registry for FOIA Requests
"""

# Django
from django.db.models import Q

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.foia.models import FOIAMultiRequest, FOIARequest, FOIASavedSearch


class FOIARequestAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Creates an autocomplete field for picking FOIA requests"""
    choices = FOIARequest.objects.all().select_related('agency__jurisdiction')
    choice_template = 'autocomplete/foia.html'
    search_fields = ['title', 'pk']
    attrs = {
        'placeholder': 'Search for requests',
        'data-autocomplete-minimum-characters': 3
    }

    def complex_condition(self, string):
        """Returns a complex set of database queries for getting requests
        by title, agency, and jurisdiction."""
        return (
            Q(title__icontains=string) | Q(agency__name__icontains=string)
            | Q(jurisdiction__name__icontains=string)
            | Q(jurisdiction__abbrev__iexact=string)
            | Q(jurisdiction__parent__abbrev__iexact=string)
        )

    def choices_for_request(self):
        query = self.request.GET.get('q', '')
        split_query = query.split()
        exclude = self.request.GET.getlist('exclude')
        # if query is an empty string, then split will produce an empty array
        # if query is an empty string, then do nto filter the existing choices
        if split_query:
            conditions = self.complex_condition(split_query[0])
            for string in split_query[1:]:
                conditions &= self.complex_condition(string)
            choices = (
                self.choices.get_viewable(self.request.user)
                .select_related('jurisdiction').select_related('agency')
                .filter(conditions).distinct()
            )
        else:
            choices = self.choices
        if exclude:
            choices = choices.exclude(pk__in=exclude)
        return self.order_choices(choices)


class FOIASavedSearchAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking your saved searches"""
    search_fields = ['title']
    attrs = {
        'placeholder': 'Saved searches',
        'data-autocomplete-minimum-characters': 0,
    }

    def choices_for_request(self):
        self.choices = FOIASavedSearch.objects.filter(user=self.request.user)
        return super(FOIASavedSearchAutocomplete, self).choices_for_request()


autocomplete_light.register(FOIARequest, FOIARequestAutocomplete)
autocomplete_light.register(FOIASavedSearch, FOIASavedSearchAutocomplete)

autocomplete_light.register(
    FOIARequest,
    name='FOIARequestAdminAutocomplete',
    choices=FOIARequest.objects.all(),
    search_fields=('title',),
    attrs={
        'placeholder': 'Search for requests',
        'data-autocomplete-minimum-characters': 1
    }
)

autocomplete_light.register(
    FOIAMultiRequest,
    name='FOIAMultiRequestAutocomplete',
    choices=FOIAMultiRequest.objects.all(),
    search_fields=('title',),
    attrs={
        'placeholder': 'Search for multirequests',
        'data-autocomplete-minimum-characters': 1
    }
)
