"""
Views for the organization application
"""
from django.contrib.auth.models import User
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from muckrock.accounts.models import Profile
from muckrock.organization.models import Organization
from muckrock.organization.forms import AddMemberForm

class Detail(DetailView):
    """Organization detail view"""
    model = Organization
    template_name="details/organization_detail.html"
    
    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(Detail, self).get_context_data(**kwargs)
        organization = context['organization']
        user = self.request.user
        member_profiles = Profile.objects.filter(organization=organization)
        member_accounts = [profile.user for profile in member_profiles]
        context['is_owner'] = user == organization.owner
        context['members'] = member_accounts
        context['form'] = AddMemberForm()
        return context

class List(ListView):
    """List of organizations"""
    model = Organization
    template_name="lists/organization_list.html"
    paginate_by = 25