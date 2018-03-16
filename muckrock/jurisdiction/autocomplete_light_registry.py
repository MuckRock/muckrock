"""
Autocomplete registry for Jurisdiction
"""

# Django
from django.db.models import BooleanField, Q, Value

# Standard Library
import re
from copy import copy

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.jurisdiction.models import Jurisdiction


class LocalAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking local jurisdictions"""
    attrs = {
        'placeholder': 'City or county name?',
        'data-autocomplete-minimum-characters': 3
    }

    def choices_for_request(self):
        choices = self.choices.all().filter(level='l', hidden=False)
        query = self.request.GET.get('q', '')
        query = query.split(', ')
        local = query[0]
        state = None
        if len(query) > 1:
            state = query[1]
            parents = Jurisdiction.objects.filter(
                level='s', abbrev__icontains=state
            )
        if local:
            choices = choices.filter(
                Q(name__icontains=local) | Q(aliases__icontains=local)
            )
        if state:
            choices = choices.filter(parent__in=parents)
        return self.order_choices(choices)[0:self.limit_choices]


autocomplete_light.register(
    Jurisdiction,
    name='StateAutocomplete',
    choices=Jurisdiction.objects.filter(level='s', hidden=False),
    search_fields=['name', 'aliases'],
    attrs={
        'placeholder': 'State name?',
        'data-autocomplete-minimum-characters': 1
    }
)

autocomplete_light.register(
    Jurisdiction,
    name='FederalStateAutocomplete',
    choices=Jurisdiction.objects.filter(level__in=('s', 'f'), hidden=False),
    search_fields=['name', 'aliases'],
    attrs={
        'placeholder': 'Jurisdiction name?',
        'data-autocomplete-minimum-characters': 1
    }
)


class JurisdictionAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Allows autocompletes against all visible jurisdictions in database"""
    choices = Jurisdiction.objects.filter(hidden=False).order_by(
        '-level', 'name'
    )
    search_fields = ['^name', 'abbrev', 'full_name', 'aliases']
    attrs = {
        'data-autocomplete-minimum-characters': 1,
        'placeholder': 'Search jurisdictions',
    }


class JurisdictionStateInclusiveAutocomplete(
    autocomplete_light.AutocompleteModelTemplate
):
    """Adds include local option for states"""
    choice_template = 'autocomplete/jurisdiction_inclusive.html'
    choices = Jurisdiction.objects.filter(hidden=False).order_by(
        '-level', 'name'
    )
    search_fields = ['^name', 'abbrev', 'full_name', 'aliases']
    attrs = {
        'data-autocomplete-minimum-characters': 1,
        'placeholder': 'Search jurisdictions',
    }
    value_format = re.compile(r'\d+-(True|False)')

    def choice_value(self, choice):
        """Value is the pk as well as if we are including local or not"""
        return '{}-{}'.format(choice.pk, choice.include_local)

    def choices_for_values(self):
        """The choices must be annotated with the include local flag"""
        assert self.choices is not None, 'choices should be a queryset'
        # filter out anything without a dash
        values = [x for x in self.values if self.value_format.match(x)]
        inc_local_values = [
            x.split('-')[0]
            for x in values
            if x != '' and x.split('-')[1] == 'True'
        ]
        dont_inc_local_values = [
            x.split('-')[0]
            for x in values
            if x != '' and x.split('-')[1] == 'False'
        ]
        inc_local_choices = (
            self.choices.filter(pk__in=[x for x in inc_local_values])
            .annotate(include_local=Value(True, output_field=BooleanField()))
        )
        dont_inc_local_choices = (
            self.choices.filter(pk__in=[x for x in dont_inc_local_values])
            .annotate(include_local=Value(False, output_field=BooleanField()))
        )
        return list(inc_local_choices) + list(dont_inc_local_choices)

    def choices_for_request(self):
        """
        This is where we add in the "include local" choices for states
        We also must get the exclude parameter into the correct form
        """
        query = self.request.GET.get('q', '')
        exclude = [
            x.split('-')[0]
            for x in self.request.GET.getlist('exclude')
            if self.value_format.match(x)
        ]

        conditions = self._choices_for_request_conditions(
            query,
            self.search_fields,
        )

        choices = (
            self.order_choices(
                self.choices.filter(conditions).exclude(pk__in=exclude)
            )[:self.limit_choices]
        )

        new_choices = []
        for choice in choices:
            choice.include_local = False
            new_choices.append(choice)
            if choice.level == 's':
                choice = copy(choice)
                choice.include_local = True
                new_choices.append(choice)
        return new_choices[:self.limit_choices]


autocomplete_light.register(Jurisdiction, JurisdictionAutocomplete)
autocomplete_light.register(Jurisdiction, LocalAutocomplete)
autocomplete_light.register(
    Jurisdiction,
    name='JurisdictionAdminAutocomplete',
    choices=Jurisdiction.objects.order_by('-level', 'name'),
    search_fields=['name', 'full_name', 'aliases'],
    attrs={
        'placeholder': 'Jurisdiction?',
        'data-autocomplete-minimum-characters': 2
    }
)
autocomplete_light.register(
    Jurisdiction, JurisdictionStateInclusiveAutocomplete
)
