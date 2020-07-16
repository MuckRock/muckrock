"""Customized autocomplete widgets"""

# Third Party
from dal import autocomplete


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


class ModelSelect2(MRSelect2Mixin, autocomplete.ModelSelect2):
    """MuckRock Model Select2"""


class ModelSelect2Multiple(MRSelect2Mixin, autocomplete.ModelSelect2Multiple):
    """MuckRock Model Select2"""
