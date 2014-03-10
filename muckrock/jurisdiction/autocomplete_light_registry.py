"""
Autocomplete registry for Jurisdiction
"""

import autocomplete_light

from muckrock.jurisdiction.models import Jurisdiction

autocomplete_light.register(Jurisdiction, name='LocalAutocomplete',
                            choices=Jurisdiction.objects.filter(level='l', hidden=False),
                            attrs={'placeholder': 'City name?',
                                   'data-autocomplete-minimum-characters': 2})

