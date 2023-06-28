"""
Detail view for a FOIA Log
"""

# Django
from django.views.generic import DetailView
from muckrock.core.views import ModelFilterMixin, MRListView

# MuckRock
from muckrock.foia.models.log import FOIALog
from muckrock.foia.filters import FOIALogFilterSet

class FOIALogDetail(DetailView):
    """Details of a single FOIA Log"""

    model = FOIALog
    context_object_name = "foia_log"
    pk_url_kwarg = "idx"
    template_name = "foia/foia_log/detail.html"

class FOIALogList(ModelFilterMixin, MRListView):
    """Filterable list of FOIA logs"""

    model = FOIALog
    template_name = "foia/foia_log/list.html"
    foia = None
    filter_class = FOIALogFilterSet
    title = "FOIA Logs"
    