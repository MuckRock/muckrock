"""
Autocomplete registry for Agency
"""

import autocomplete_light
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction

class AgencyAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking agencies"""
    search_fields = ['name', 'aliases']
    attrs = {
        'data-autocomplete-minimum-characters': 0
    }
    def choices_for_request(self):
        query = self.request.GET.get('q', '')
        jurisdiction_id = self.request.GET.get('jurisdiction_id', None)

        conditions = self._choices_for_request_conditions(query, self.search_fields)
        choices = self.choices.filter(conditions, status='approved')
        if jurisdiction_id:
            if jurisdiction_id == 'f':
                jurisdiction_id = (Jurisdiction.objects.filter(level='f')[0]).id
            choices = self._filter_by_jurisdiction(choices, jurisdiction_id)

        return self.order_choices(choices)[0:self.limit_choices]

    def _filter_by_jurisdiction(self, choices, jurisdiction_id):
        """Filter the agency choices given a jurisdiction"""
        return choices.filter(jurisdiction_id=jurisdiction_id)

#pylint: disable=interface-not-implemented
class AgencyAdminAutocomplete(AgencyAutocomplete):
    """Autocomplete for Agencies for FOIA admin page"""
    attrs = {'placeholder': 'Agency?'}


class AgencyAppealAdminAutocomplete(AgencyAdminAutocomplete):
    """Autocomplete for Appeal Agencies - allows local agencies to pick
    state agencies as their appeal agency"""

    def _filter_by_jurisdiction(self, choices, jurisdiction_id):
        """Filter the agency choices given a jurisdiction"""
        jurisdiction = Jurisdiction.objects.get(pk=jurisdiction_id)
        if jurisdiction.level == 'l':
            # For local jurisdictions, appeal agencies may come from the
            # parent level
            return choices.filter(
                    jurisdiction__in=(jurisdiction, jurisdiction.parent))
        else:
            return choices.filter(jurisdiction=jurisdiction)


autocomplete_light.register(Agency, AgencyAutocomplete)
autocomplete_light.register(Agency, AgencyAdminAutocomplete)
autocomplete_light.register(Agency, AgencyAppealAdminAutocomplete)
