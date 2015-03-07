"""
Autocomplete registry for FOIA Requests
"""

from muckrock.foia.models import FOIARequest

import autocomplete_light

autocomplete_light.register(
    FOIARequest,
    name='FOIARequestAdminAutocomplete',
    choices=FOIARequest.objects.all(),
    search_fields=('title',),
    attrs={
        'placeholder': 'Search for requests',
        'data-autocomplete-minimum-characters': 1})
