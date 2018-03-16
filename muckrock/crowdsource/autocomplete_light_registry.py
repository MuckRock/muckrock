"""
Autocomplete registry for crowdsources
"""

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.crowdsource.models import Crowdsource


class CrowdsourceDraftAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete for picking crowdsources"""
    search_fields = ['title', 'description']
    attrs = {
        'placeholder': 'Choose an unstarted crowdsource',
        'data-autocomplete-minimum-characters': 1
    }

    def choices_for_request(self):
        """
        Only show crowdsources owned by the user
        """
        self.choices = Crowdsource.objects.filter(
            status='draft',
            user=self.request.user,
        )
        return super(CrowdsourceDraftAutocomplete, self).choices_for_request()


autocomplete_light.register(Crowdsource, CrowdsourceDraftAutocomplete)
