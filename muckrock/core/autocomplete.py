"""Customized autocomplete widgets"""

# Standard Library
import re

# Third Party
from dal import autocomplete

# MuckRock
from muckrock.jurisdiction.models import Jurisdiction


class MRSelect2Mixin:
    """MuckRock Model Select2 mixin"""

    def __init__(self, *args, **kwargs):
        attrs = {
            "data-html": True,
            "data-dropdown-css-class": "select2-dropdown",
            "data-width": "100%",
        }
        attrs.update(kwargs.pop("attrs", {}))
        super().__init__(*args, attrs=attrs, **kwargs)

    def filter_choices_to_render(self, selected_choices):
        """Filter out non-numeric choices"""
        selected_choices = [c for c in selected_choices if c.isdecimal()]
        return super().filter_choices_to_render(selected_choices)


class ModelSelect2(MRSelect2Mixin, autocomplete.ModelSelect2):
    """MuckRock Model Select2"""


class ModelSelect2Multiple(MRSelect2Mixin, autocomplete.ModelSelect2Multiple):
    """MuckRock Model Select2"""


class Select2MultipleSI(MRSelect2Mixin, autocomplete.Select2Multiple):
    """MuckRock Select2 for state inclusive jurisdiction autocomplete"""

    value_format = re.compile(r"\d+-(True|False)")

    def filter_choices_to_render(self, selected_choices):
        """Replace self.choices with selected_choices."""
        self.choices = []
        for choice in selected_choices:
            if not self.value_format.match(choice):
                continue
            pk, include_local = choice.split("-")
            jurisdiction = Jurisdiction.objects.get(pk=pk)
            label = str(jurisdiction)
            if include_local == "True":
                label += " (include local)"
            self.choices.append((choice, label))
