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

from muckrock.organization.models import Organization
from muckrock.organization.forms import OrganizationForm, AddMembersForm
from muckrock.settings import STRIPE_PUB_KEY, MONTHLY_REQUESTS

from datetime import datetime

class Detail(DetailView):
    """Organization detail view"""
    model = Organization
    template_name = "details/organization_detail.html"

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(Detail, self).get_context_data(**kwargs)
        organization = context['organization']
        user = self.request.user
        member_accounts = [profile.user for profile in organization.get_members()]
        context['is_staff'] = user.is_staff
        context['is_owner'] = organization.is_owned_by(user)
        context['is_member'] = user.get_profile().is_member_of(organization)
        context['members'] = member_accounts
        context['form'] = AddMembersForm()
        return context

    def post(self, request, **kwargs):
        # pylint: disable=line-too-long
        """Handle form submission for adding and removing users"""
        organization = get_object_or_404(Organization, slug=kwargs['slug'])
        action = request.POST.get('action', '')
        if action == 'add_members':
            form = AddMembersForm(request.POST)
            if form.is_valid():
                new_members = form.cleaned_data['add_members']
                added_members = 0
                for new_member in new_members:
                    if not organization.is_owned_by(new_member):
                        organization.add_member(new_member)
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
                if not organization.is_owned_by(user):
                    organization.remove_member(user)
                    removed_members += 1
            if removed_members == 1:
                messages.success(request, 'You revoked membership from 1 person.')
            elif removed_members > 1:
                messages.success(request, 'You revoked membership from %s people.' % removed_members)
        elif action == 'change_subscription':
            if organization.is_active():
                organization.pause_subscription()
                msg = 'Your subscription is paused. You may resume it at any time.'
            else:
                organization.start_subscription()
                msg = 'Your subscription is reactivated.'
            messages.success(request, msg)
        else:
            messages.error(request, 'This action is not available.')
        return redirect(organization)

class List(ListView):
    """List of organizations"""
    model = Organization
    template_name = "lists/organization_list.html"
    paginate_by = 25

@login_required
def create_organization(request):
    """Creates an organization, setting the user who created it as the owner"""
    if request.method == 'POST':        
        form = OrganizationForm(request.POST)
        if form.is_valid():
            # TODO: Add payments to org creation
            stripe_token = request.POST.get('stripe_token', None)
            current_user = request.user
            customer = current_user.get_profile().customer()
            customer.card = stripe_token
            customer.save()
            organization = form.save(commit=False)
            organization.slug = slugify(organization.name)
            organization.owner = current_user
            organization.stripe_id = current_user.get_profile().stripe_id
            organization.num_requests = MONTHLY_REQUESTS.get('org', 0)
            organization.date_update = datetime.now()
            organization.save()
            organization.start_subscription()
            messages.success(request, 'Your organization has been created.')
            return redirect(organization)
    else:
        form = OrganizationForm()
    
    # check if user already owns an org
    other_org = Organization.objects.filter(owner=request.user)
    if other_org:
        messages.error(request, 'You can only own one organization at a time.')
        return redirect('org-index')

    context = {
        'form': form,
        'stripe_pk': STRIPE_PUB_KEY
    }

    return render_to_response(
        'forms/organization/create.html',
        context,
        context_instance=RequestContext(request)
    )

def delete_organization(request, **kwargs):
    """Deletes an organization by removing its users and cancelling its plan"""
    organization = get_object_or_404(Organization, slug=kwargs['slug'])
    if organization.is_owned_by(request.user) or request.user.is_staff:
        members = organization.get_members()
        for member in members:
            member.organization = None
        organization.delete()
        messages.success(request, 'Your organization was deleted.')
    elif request.user.get_profile().is_member_of(organization):
        messages.error(request, 'Only the owner may delete this organization.')
    else:
        messages.error(request, 'You do not have permission to access this organization.')
    return redirect('org-index')
