"""
Views for the organization application
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView


from muckrock.accounts.models import Profile
from muckrock.organization.models import Organization
from muckrock.organization.forms import OrganizationForm, AddMembersForm

from datetime import datetime

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
        context['form'] = AddMembersForm()
        return context
    
    def post(self, request, **kwargs):
        """Handle form submission for adding and removing users"""
        organization = get_object_or_404(Organization, slug=kwargs['slug'])
        action = request.POST.get('action', '')
        if action == 'add_members':
            form = AddMembersForm(request.POST)
            if form.is_valid():
                organization = Organization.objects.get(slug=kwargs['slug'])
                new_members = form.cleaned_data['add_members']
                added_members = 0
                for new_member in new_members:
                    if not organization.is_owned_by(new_member):                    
                        profile = new_member.get_profile()
                        profile.organization = organization
                        profile.save()
                        added_members += 1
                if added_members == 1:
                    messages.success(request, 'You granted membership to 1 person.')
                elif added_members > 1:
                    messages.success(request, 'You granted membership to %s people.' % added_members)
        elif action == 'remove_members':
            members = request.POST.getlist('members')
            removed_members = 0
            for uid in members:
                user = User.objects.get(pk=uid)
                profile = user.get_profile()
                profile.organization = None
                profile.save()
                removed_members += 1
            if removed_members == 1:
                messages.success(request, 'You revoked membership from 1 person.')
            elif removed_members > 1:
                messages.success(request, 'You revoked membership from %s people.' % removed_members)
        elif action == '':
            pass
        else:
            messages.error(request, 'This action is not available.')
        return redirect(organization)
            

class List(ListView):
    """List of organizations"""
    model = Organization
    template_name="lists/organization_list.html"
    paginate_by = 25

@login_required
def create_organization(request):
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            current_user = request.user
            organization = form.save(commit=False)
            organization.slug = slugify(organization.name)
            organization.owner = current_user
            organization.stripe_id = current_user.get_profile().stripe_id
            organization.date_update = datetime.now()
            organization.save()
            messages.success(request, 'Your organization has been created.')
            return redirect(organization)
    else:
        form = OrganizationForm()
    
    context = {
        'form': form
    }

    return render_to_response(
        'forms/organization/create.html',
        context,
        context_instance=RequestContext(request)
    )

def delete_organization(request, **kwargs):
    organization = get_object_or_404(Organization, slug=kwargs['slug'])
    if organization.is_owned_by(request.user):
        # delete the org
        messages.success(request, 'Your organization was deleted.')
    elif request.user.get_profile().is_member_of(organization):
        messages.error(request, 'Only the owner may delete this organization.')
    else:
        messages.error(request, 'You do not have permission to access this organization.')
    return redirect(organization)