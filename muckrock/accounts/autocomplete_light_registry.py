"""
Autocomplete registry for Accounts
"""

from django.contrib.auth.models import User

import autocomplete_light

autocomplete_light.register(User, name='UserAdminAutocomplete',
                            choices=User.objects.all(),
                            search_fields=('username',),
                            attrs={'placeholder': 'User?',
                                   'data-autocomplete-minimum-characters': 1})

