"""
Views for the organization application
"""

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from muckrock.organization.models import Organization

class Detail(DetailView):
    """Organization detail view"""
    model = Organization
    template_name="lists/organization_list.html"


class List(ListView):
    """List of organizations"""
    model = Organization
    template_name="details/organization_details.html"
    paginate_by = 25