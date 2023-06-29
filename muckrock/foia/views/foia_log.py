"""
Detail view for a FOIA Log
"""

# Django
from django.views.generic import DetailView

# MuckRock
from muckrock.core.views import ModelFilterMixin, MRListView
from muckrock.foia.filters import FOIALogFilterSet
from muckrock.foia.models.log import FOIALog


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
