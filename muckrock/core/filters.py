"""
Filters and widgets shared between applications.
"""

# Third Party
import django_filters

# MuckRock
from muckrock.core.forms import NativeDateInput
from muckrock.foia.models import STATUS

BLANK_STATUS = [("", "All")] + STATUS
NULL_BOOLEAN_CHOICES = [(None, "----------"), (True, "Yes"), (False, "No")]
BOOLEAN_CHOICES = [(True, "Yes"), (False, "No")]


class DateRangeWidget(django_filters.widgets.RangeWidget):
    """A from/to pair of native date inputs"""

    template_name = "lib/widgets/date_range.html"

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.widgets = [NativeDateInput(), NativeDateInput()]
