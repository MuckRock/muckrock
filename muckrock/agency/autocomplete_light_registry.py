"""
Autocomplete registry for Agency
"""

from django.db.models import Q

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction


class AgencyAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking agencies"""
    search_fields = ['name', 'aliases']
    attrs = {
        'data-autocomplete-minimum-characters': 1,
        'placeholder': 'Search agencies'
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
        #pylint: disable=no-self-use
        return choices.filter(jurisdiction_id=jurisdiction_id)


class AgencyMultiRequestAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Provides an autocomplete field for picking multiple agencies."""
    choices = (Agency.objects.get_approved().select_related('jurisdiction__parent')
                                            .prefetch_related('types'))
    choice_template = 'autocomplete/agency.html'
    search_fields = ['name']
    attrs = {
        'placeholder': 'Search by agency or jurisdiction',
        'data-autocomplete-minimum-characters': 2
    }

    def complex_condition(self, string):
        """Returns a complex set of database queries for getting agencies
        by name, alias, jurisdiction, jurisdiction abbreviation, and type."""
        # pylint: disable=no-self-use
        return (Q(name__icontains=string)|
                Q(aliases__icontains=string)|
                Q(jurisdiction__name__icontains=string)|
                Q(jurisdiction__abbrev__iexact=string)|
                Q(jurisdiction__parent__abbrev__iexact=string)|
                Q(types__name__icontains=string))

    def choices_for_request(self):
        query = self.request.GET.get('q', '')
        split_query = query.split()
        # if query is an empty string, then split will produce an empty array
        # if query is an empty string, then do nto filter the existing choices
        if split_query:
            conditions = self.complex_condition(split_query[0])
            for string in split_query[1:]:
                conditions &= self.complex_condition(string)
            choices = self.choices.filter(conditions).distinct()
        else:
            choices = self.choices
        return self.order_choices(choices)[0:self.limit_choices]

class AgencyAdminAutocomplete(AgencyAutocomplete):
    """Autocomplete for Agencies for FOIA admin page"""
    attrs = {'placeholder': 'Agency?'}


class AgencyAppealAdminAutocomplete(AgencyAdminAutocomplete):
    """Autocomplete for Appeal Agencies - allows local agencies to pick
    state agencies as their appeal agency"""

    def _filter_by_jurisdiction(self, choices, jurisdiction_id):
        """Filter the agency choices given a jurisdiction"""
        #pylint: disable=no-self-use
        jurisdiction = Jurisdiction.objects.get(pk=jurisdiction_id)
        if jurisdiction.level == 'l':
            # For local jurisdictions, appeal agencies may come from the
            # parent level
            return choices.filter(
                    jurisdiction__in=(jurisdiction, jurisdiction.parent))
        else:
            return choices.filter(jurisdiction=jurisdiction)



autocomplete_light.register(Agency, AgencyAutocomplete)
autocomplete_light.register(Agency, AgencyMultiRequestAutocomplete)
autocomplete_light.register(Agency, AgencyAdminAutocomplete)
autocomplete_light.register(Agency, AgencyAppealAdminAutocomplete)
