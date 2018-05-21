"""
Autocomplete registry for Agency
"""

# Django
from django.db.models import Count, Q

# Standard Library
import logging
import re
from string import capwords

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
        Agency.objects.select_related('jurisdiction__parent').only(
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
        'placeholder': 'Agency\'s name, followed by location',
        'data-autocomplete-minimum-characters': 2,
    }

    def choices_for_request(self):
        query = self.request.GET.get('q', '')
        exclude = self.request.GET.getlist('exclude')
        # remove "new" agencies from exclude list, as they do not have
        # valid PKs to filter on
        exclude = [e for e in exclude if re.match(r'[0-9]+', e)]
        conditions = self._choices_for_request_conditions(
            query,
            self.search_fields,
        )
        choices = self.order_choices(
            self.choices.get_approved_and_pending(
                self.request.user
            ).filter(conditions).exclude(pk__in=exclude)
        )[0:self.limit_choices]

        query, jurisdiction = self._split_jurisdiction(query)
        fuzzy_choices = self._fuzzy_choices(
            query,
            exclude,
            jurisdiction,
            choices,
        )
        choices = list(choices) + [c[2] for c in fuzzy_choices]
        new_agency = self._create_new_agency(query, jurisdiction, choices)
        if new_agency is not None:
            choices.append(new_agency)
        return choices

    def _fuzzy_choices(self, query, exclude, jurisdiction, choices):
        """Do fuzzy matching for additional choices"""
        exclude = exclude + [c.pk for c in choices]
        choices = (
            self.choices.get_approved_and_pending(self.request.user)
            .filter(jurisdiction=jurisdiction).exclude(pk__in=exclude)
        )
        return process.extractBests(
            query,
            {a: a.name
             for a in choices},
            scorer=fuzz.partial_ratio,
            score_cutoff=83,
            limit=10,
        )

    def _create_new_agency(self, query, jurisdiction, choices):
        """If there are no exact matches, give the option to create a new one"""
        if not query.lower() in [c.name.lower() for c in choices]:
            name = re.sub(r'\$', '', capwords(query))
            new_agency = Agency(
                name=name,
                jurisdiction=jurisdiction,
                status='pending',
            )
            return new_agency
        else:
            return None

    def _split_jurisdiction(self, query):
        """Try to pull a jurisdiction out of an unmatched query"""
        comma_split = query.split(',')
        if len(comma_split) > 2:
            locality, state = [w.strip() for w in comma_split[-2:]]
            name = ','.join(comma_split[:-2])
            try:
                jurisdiction = Jurisdiction.objects.get(
                    Q(parent__name__iexact=state)
                    | Q(parent__abbrev__iexact=state),
                    name__iexact=locality,
                    level='l',
                )
                return name, jurisdiction
            except Jurisdiction.DoesNotExist:
                pass
        if len(comma_split) > 1:
            state = comma_split[-1].strip()
            name = ','.join(comma_split[:-1])
            try:
                jurisdiction = Jurisdiction.objects.get(
                    Q(name__iexact=state) | Q(abbrev__iexact=state),
                    level='s',
                )
                return name, jurisdiction
            except Jurisdiction.DoesNotExist:
                jurisdiction = Jurisdiction.objects.filter(
                    name__iexact=state,
                    level='l',
                ).annotate(
                    count=Count('agencies__foiarequest'),
                ).order_by('-count').first()
                if jurisdiction is not None:
                    return name, jurisdiction
        return query, Jurisdiction.objects.get(level='f')

    def validate_values(self):
        """Handle validating new agencies"""
        p_existing = re.compile(r'[0-9]')
        p_new = re.compile(r'\$new\$[^$]+\$[0-9]+\$')
        existing = [v for v in self.values if p_existing.match(v)]
        new = [v for v in self.values if p_new.match(v)]
        # all values should be existing PK's or a new agency in the proper format
        if len(existing) + len(new) != len(self.values):
            return False
        # all existing should be valid choices
        return len(existing) == self.choices.get_approved_and_pending(
            self.request.user
        ).filter(pk__in=existing).count()

    def choices_for_values(self):
        """Overridden to not crash on invalid PKs in values"""
        assert self.choices is not None, 'choices should be a queryset'
        return self.choices.filter(
            pk__in=[
                x for x in self.values
                if not isinstance(x, basestring) or re.match(r'[0-9]+', x)
            ]
        )

    def order_choices(self, choices):
        """Order choices by popularity"""
        return choices.annotate(count=Count('foiarequest')).order_by('-count')


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
