"""
Autocomplete registry for Portal
"""

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.portal.models import Portal


autocomplete_light.register(
        Portal,
        name='PortalAutocomplete',
        choices=Portal.objects.all(),
        search_fields=('name', 'url'),
        attrs={
            'placeholder': 'Search for a portal',
            'data-autocomplete-minimum-characters': 1,
            })
