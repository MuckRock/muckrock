"""
Autocomplete registry for Organization
"""

import autocomplete_light
from django.contrib.auth.models import User

class UserAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking agencies"""
    search_fields = ['username', 'email']
    attrs = {
        'placeholder': 'Username or email',
        'data-autocomplete-minimum-characters': 2
    }

autocomplete_light.register(User, UserAutocomplete)
