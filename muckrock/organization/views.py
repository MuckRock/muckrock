"""
Views for the organization application
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, DetailView

import actstream
from datetime import datetime
import logging
import stripe

from muckrock.organization.models import Organization
from muckrock.organization.forms import OrganizationCreateForm, \
                                        OrganizationUpdateForm, \
                                        AddMembersForm
from muckrock.settings import STRIPE_PUB_KEY


class OrganizationListView(ListView):
    """List of organizations"""
    model = Organization
    template_name = "organization/list.html"
    paginate_by = 25


class OrganizationCreateView(CreateView):
    """
    Presents a form for creating an organization.
    At the moment, only staff may create organizations.
    """
    form_class = OrganizationCreateForm
    template_name = 'organization/create.html'

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """At the moment, only staff are allowed to create an org."""
        return super(OrganizationCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        When form is valid, save it.
        Then, make the owner a member of the organization.
        Then, redirect to the newly created organization.
        """
        organization = form.save()
        # make owner a member
        owner = organization.owner
        owner.profile.organization = organization
        owner.profile.save()
        # redirect to the success url with a nice message
        logging.info('%s created %s', self.request.user, organization)
        messages.success(self.request, 'The organization has been created. Excellent!')
        return redirect(organization.get_absolute_url())


class OrganizationDetailView(DetailView):
    """Organization detail view"""
    model = Organization
    template_name = "organization/detail.html"

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(OrganizationDetailView, self).get_context_data(**kwargs)
        organization = context['organization']
        user = self.request.user
        member_accounts = [profile.user for profile in organization.members.all()]
        if user.is_authenticated():
            context['is_staff'] = user.is_staff
            context['is_owner'] = organization.is_owned_by(user)
            context['is_member'] = user.profile.is_member_of(organization)
        else:
            context['is_staff'] = False
            context['is_owner'] = False
            context['is_member'] = False
        context['members'] = member_accounts
        context['form'] = AddMembersForm()
        context['sidebar_admin_url'] = reverse(
            'admin:organization_organization_change',
            args=(organization.pk,))
        return context

    def post(self, request, **kwargs):
        # pylint: disable=no-self-use
        """Handle form submission for adding and removing users"""
        organization = get_object_or_404(Organization, slug=kwargs['slug'])
        action = request.POST.get('action', '')
        if action == 'add_members':
            _add_members(request, organization)
        elif action == 'remove_members':
            _remove_members(request, organization)
        elif action == 'change_subscription':
            if organization.is_active():
                organization.pause_subscription()
                msg = 'Your subscription is paused. You may resume it at any time.'
            else:
                try:
                    organization.start_subscription()
                except (stripe.InvalidRequestError, stripe.CardError, ValueError) as exception:
                    messages.error(request, exception)
                    return redirect(organization)
                msg = 'Your subscription is reactivated.'
            messages.success(request, msg)
        else:
            messages.error(request, 'This action is not available.')
        return redirect(organization)

def _add_members(request, organization):
    """A helper function to add a list of members to an organization"""
    form = AddMembersForm(request.POST)
    if form.is_valid():
        new_members = form.cleaned_data['add_members']
        new_member_count = len(new_members)
        existing_member_count = organization.members.count()
        # limit org membership to 50 users
        if new_member_count <= (50 - existing_member_count):
            for new_member in new_members:
                organization.add_member(new_member)
                actstream.action.send(
                    request.user,
                    verb='added',
                    action_object=new_member,
                    target=organization
                )
            msg = 'You granted membership to %s ' % new_member_count
            msg += 'person.' if new_member_count == 1 else 'people.'
            messages.success(request, msg)
        else:
            error_msg = ('You currently have %s members in your organization '
                         'but you are limited to 50. If you want to exceed this '
                         'limit, please contact us at info@muckrock.com' % existing_member_count)
            messages.error(request, error_msg)
    return

def _remove_members(request, organization):
    """A helper function to remove a list of members from an organization"""
    members = request.POST.getlist('members')
    member_count = len(members)
    for uid in members:
        user = User.objects.get(pk=uid)
        organization.remove_member(user)
        actstream.action.send(
            request.user,
            verb='removed',
            action_object=user,
            target=organization
        )
    msg = 'You revoked membership from %s ' % member_count
    msg += 'person.' if member_count == 1 else 'people.'
    messages.success(request, msg)

def activate_organization(request, **kwargs):
    """Grants an organization requests and subscribes its owner to a recurring payment plan."""
    organization = get_object_or_404(Organization, slug=kwargs['slug'])
    # first check if the org is already active
    if organization.is_active():
        messages.error(request, 'This organization is already active.')
        return redirect(organization)
    # next check if the user has the authority
    if not organization.is_owned_by(request.user) and not request.user.is_staff:
        messages.error(request, 'Only this organization\'s owner may activate it.')
        return redirect(organization)
    # finally, actually activate the organization
    if request.method == 'POST':
        token = request.POST.get('token', None)
        if token:
            # update owner card with token
            customer = organization.owner.profile.customer()
            customer.card = token
            # create plan
            try:
                organization.create_plan()
            except ValueError as exception:
                messages.error(request, exception)
                return redirect(organization)
            # subscribe owner to plan
            organization.start_subscription()
    return redirect(organization)

def deactivate_organization(request, **kwargs):
    """Unsubscribes its owner from the recurring payment plan."""
    organization = get_object_or_404(Organization, slug=kwargs['slug'])
    # first check if org is already deactivated
    if not organization.is_active():
        messages.error(request, 'This organization is already inactive.')
        return redirect(organization)
    # next check if the user has the authority
    if not organization.is_owned_by(request.user) and not request.user.is_staff:
        messages.error(request, 'Only this organization\'s owner may deactivate it.')
        return redirect(organization)
    # finally, actually deactivate the organization
    if request.method == 'POST':
        organization.pause_subscription()
    return redirect(organization)

def delete_organization(request, **kwargs):
    """Deletes an organization by removing its users and cancelling its plan"""
    organization = get_object_or_404(Organization, slug=kwargs['slug'])
    if organization.is_owned_by(request.user) or request.user.is_staff:
        members = organization.members.all()
        for member in members:
            member.organization = None
            member.save()
        organization.pause_subscription()
        try:
            organization.delete_plan()
        except ValueError as exception:
            messages.error(request, exception)
            return redirect(organization)
        organization.delete()
        messages.success(request, 'Your organization was deleted.')
    elif request.user.profile.is_member_of(organization):
        messages.error(request, 'Only the owner may delete this organization.')
    else:
        messages.error(request, 'You do not have permission to access this organization.')
    return redirect('org-index')

@user_passes_test(lambda u: u.is_staff)
def update_organization(request, **kwargs):
    """Updates the monthly requests, monthly cost, and max users for an org"""
    organization = get_object_or_404(Organization, slug=kwargs['slug'])
    old_cost = organization.monthly_cost
    if request.method == 'POST':
        form = OrganizationUpdateForm(request.POST, instance=organization)
        if form.is_valid():
            organization = form.save()
            if old_cost != organization.monthly_cost:
                try:
                    organization.update_plan()
                except (stripe.InvalidRequestError, stripe.CardError, ValueError) as exception:
                    messages.error(request, exception)
                    return redirect(organization)
            messages.success(request, 'The organization was updated.')
            return redirect(organization)
    else:
        form = OrganizationUpdateForm(instance=organization)
    return render_to_response(
        'forms/base_form.html',
        {'form': form},
        context_instance=RequestContext(request)
    )

