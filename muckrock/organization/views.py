"""
Views for the organization application
"""

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from muckrock.organization.models import Organization

class Detail(DetailView):
    """Organization detail view"""
    model = Organization


class List(ListView):
    """List of organizations"""
    paginate_by = 25
    model = Organization
