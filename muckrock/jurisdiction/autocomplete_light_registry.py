"""
Autocomplete registry for Jurisdiction
"""

import autocomplete_light
from muckrock.jurisdiction.models import Jurisdiction

autocomplete_light.register(
    Jurisdiction,
    name='LocalAutocomplete',
    choices=Jurisdiction.objects.filter(level='l', hidden=False),
    attrs={
        'placeholder': 'City name?',
        'data-autocomplete-minimum-characters': 3
    }
)

autocomplete_light.register(
    Jurisdiction,
    name='StateAutocomplete',
    choices=Jurisdiction.objects.filter(level='s', hidden=False),
    attrs={
        'placeholder': 'State name?',
        'data-autocomplete-minimum-characters': 1
    }
)

autocomplete_light.register(
    Jurisdiction,
    name='JurisdictionAutocomplete',
    choices=Jurisdiction.objects.filter(hidden=False),
    attrs={
        'placeholder': 'Jurisdiction',
        'data-autocomplete-minimum-characters': 2
    }
)