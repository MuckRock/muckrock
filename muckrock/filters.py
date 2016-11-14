"""
Filters and widgets shared between applications.
"""

import django_filters

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
        """ % {'inputs': '\n'.join(rendered_widgets)}
