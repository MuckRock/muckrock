"""
Autocomplete registry for Jurisdiction
"""

from autocomplete_light import shortcuts as autocomplete_light
from muckrock.jurisdiction.models import Jurisdiction

class LocalAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking local jurisdictions"""
    attrs = {
        'placeholder': 'City or county name?',
        'data-autocomplete-minimum-characters': 3
    }
    def choices_for_request(self):
        choices = self.choices.all().filter(level='l', hidden=False)
        query = self.request.GET.get('q', '')
        query = query.split(', ')
        local = query[0]
        state = None
        if len(query) > 1:
            state = query[1]
            parents = Jurisdiction.objects.filter(level='s', abbrev__icontains=state)
        if local:
            choices = choices.filter(name__icontains=local)
        if state:
            choices = choices.filter(parent__in=parents)
        return self.order_choices(choices)[0:self.limit_choices]

autocomplete_light.register(
    Jurisdiction,
    name='StateAutocomplete',
    choices=Jurisdiction.objects.filter(level='s', hidden=False),
    attrs={
        'placeholder': 'State name?',
        'data-autocomplete-minimum-characters': 1
    }
)

class JurisdictionAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Allows autocompletes against all visible jurisdictions in database"""
    choices = Jurisdiction.objects.filter(hidden=False).order_by('-level', 'name')
    search_fields = ['^name', 'abbrev', 'full_name']
    attrs = {
        'data-autocomplete-minimum-characters': 1,
        'placeholder': 'Search jurisdictions',
    }

autocomplete_light.register(Jurisdiction, JurisdictionAutocomplete)
autocomplete_light.register(Jurisdiction, LocalAutocomplete)
autocomplete_light.register(Jurisdiction, name='JurisdictionAdminAutocomplete',
                            choices=Jurisdiction.objects.order_by('-level', 'name'),
                            search_fields=['name', 'full_name'],
                            attrs={'placeholder': 'Jurisdiction?',
                                   'data-autocomplete-minimum-characters': 2})
