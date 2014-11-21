"""
Autocomplete registry for Agency
"""

import autocomplete_light

from muckrock.agency.models import Agency

#pylint: disable=interface-not-implemented
class AgencyAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Autocomplete for Agencies"""
    autocomplete_js_attributes = {'placeholder': 'Agency?'}

    def choices_for_request(self):
        """Filter the choices based on the jurisdiction"""
        query = self.request.GET.get('q', '')
        jurisdiction_id = self.request.GET.get('jurisdiction_id', None)

        choices = self.choices.all()
        if query:
            choices = choices.filter(name__icontains=query)
        if jurisdiction_id:
            choices = choices.filter(jurisdiction_id=jurisdiction_id)

        return self.order_choices(choices)[0:self.limit_choices]

autocomplete_light.register(Agency, AgencyAutocomplete)
