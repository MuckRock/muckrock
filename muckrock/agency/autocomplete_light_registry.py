"""
Autocomplete registry for Agency
"""

# Standard Library
import logging

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from fuzzywuzzy import fuzz, process

# MuckRock
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction

logger = logging.getLogger(__name__)


class AgencyAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Creates an autocomplete field for picking agencies"""
    choices = Agency.objects.filter(status='approved'
                                    ).select_related('jurisdiction')
    choice_template = 'autocomplete/agency.html'
    search_fields = ['name', 'aliases']
    attrs = {
        'data-autocomplete-minimum-characters': 1,
        'placeholder': 'Search agencies',
    }

    def choices_for_request(self):
        """Additionally filter choices by jurisdiction."""
        jurisdiction_id = self.request.GET.get('jurisdiction_id')
        if jurisdiction_id:
            self.choices = self._filter_by_jurisdiction(
                self.choices, jurisdiction_id
            )
        return super(AgencyAutocomplete, self).choices_for_request()

    def _filter_by_jurisdiction(self, choices, jurisdiction_id):
        """Do the filtering here so subclasses can override this method"""
        if jurisdiction_id == 'f':
            jurisdiction_id = Jurisdiction.objects.get(level='f').id
        return choices.filter(jurisdiction__id=jurisdiction_id)


class AgencyComposerAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Provides an autocomplete field for composing requests"""
    choices = (
        Agency.objects.get_approved()
        .select_related('jurisdiction__parent').only(
            'name',
            'exempt',
            'jurisdiction__name',
            'jurisdiction__level',
            'jurisdiction__parent__abbrev',
        )
    )
    choice_template = 'autocomplete/agency.html'
    split_words = 'and'
    # = prefix uses iexact match
    search_fields = [
        'name',
        'aliases',
        'types__name',
        'jurisdiction__name',
        '=jurisdiction__abbrev',
        '=jurisdiction__parent__abbrev',
    ]
    attrs = {
        'placeholder': 'Search by agency or jurisdiction',
        'data-autocomplete-minimum-characters': 2,
    }

    def choices_for_request(self):
        choices = super(AgencyComposerAutocomplete, self).choices_for_request()
        # add fuzzy matches to the options
        exclude = self.request.GET.getlist('exclude') + [c.pk for c in choices]
        fuzzy_choices = process.extractBests(
            self.request.GET.get('q', ''),
            {a: a.name
             for a in self.choices.exclude(pk__in=exclude)},
            scorer=fuzz.partial_ratio,
            score_cutoff=83,
            limit=10,
        )
        return list(choices) + [c[2] for c in fuzzy_choices]


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
                jurisdiction__in=(jurisdiction, jurisdiction.parent)
            )
        else:
            return choices.filter(jurisdiction=jurisdiction)


autocomplete_light.register(Agency, AgencyAutocomplete)
autocomplete_light.register(Agency, AgencyComposerAutocomplete)
autocomplete_light.register(Agency, AgencyAdminAutocomplete)
autocomplete_light.register(Agency, AgencyAppealAdminAutocomplete)
