"""
Filters and widgets shared between applications.
"""

# Third Party
import django_filters

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
