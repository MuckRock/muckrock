"""
Custom form fields for the FOIA app
"""

# Django
from django import forms

# Standard Library
import re

# MuckRock
from muckrock.agency.models import Agency


class ComposerAgencyField(forms.ModelMultipleChoiceField):
    """Custom field to act as a model multiple choice field that can also
    create new agencies
    """

    def _check_values(self, value):
        """Handle creating new agencies here"""
        p_new = re.compile(r'\$new\$[^$]+\$[0-9]+\$')
        new = [a for a in value if p_new.match(a)]
        other = [a for a in value if not p_new.match(a)]

        new_pks = []
        for new_agency in new:
            name, jurisdiction_pk = new_agency.split('$')[2:4]
            new_pks.append(
                Agency.objects.create_new(
                    name,
                    jurisdiction_pk,
                    self.user,
                ).pk
            )
        # TODO deal with exempt agencies
        existing_agencies = (
            super(ComposerAgencyField, self)._check_values(other)
        )
        return existing_agencies.union(Agency.objects.filter(pk__in=new_pks))
