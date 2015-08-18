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

autocomplete_light.register(
    User,
    name="ProjectContributorAutocomplete",
    choices=User.objects.filter(),
    search_fields=('username', 'first_name', 'last_name'),
    attrs={'placeholder': 'Search users'}
)
