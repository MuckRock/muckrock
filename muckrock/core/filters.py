"""
Filters and widgets shared between applications.
"""

# Third Party
import django_filters
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.foia.models import STATUS

BLANK_STATUS = [('', 'All')] + STATUS
NULL_BOOLEAN_CHOICES = [(None, '----------'), (True, 'Yes'), (False, 'No')]
BOOLEAN_CHOICES = [(True, 'Yes'), (False, 'No')]


class RangeWidget(django_filters.widgets.RangeWidget):
    """Customizes the rendered output of the RangeWidget"""

    def format_output(self, rendered_widgets):
        return """
            <div class="input-range">
                <div class="small labels nomargin">
                    <label>Since</label>
                    <label>Until</label>
                </div>
                <div class="inputs">
                    %(inputs)s
                </div>
            </div>
        """ % {
            'inputs': '\n'.join(rendered_widgets)
        }


class AutocompleteModelMultipleChoiceFilter(
    django_filters.ModelMultipleChoiceFilter
):
    """Autocomplete Filter
    Properly sets the choices on the widgets autocomplete so there is no data leak
    of underlying model titles if user manually enters invalid values
    """

    def __init__(self, *args, **kwargs):
        autocomplete = kwargs.pop('autocomplete')
        kwargs['widget'] = autocomplete_light.MultipleChoiceWidget(autocomplete)
        super(AutocompleteModelMultipleChoiceFilter,
              self).__init__(*args, **kwargs)

    def get_queryset(self, request):
        queryset = super(AutocompleteModelMultipleChoiceFilter,
                         self).get_queryset(request)
        self.widget.autocomplete.choices = queryset
        return queryset
