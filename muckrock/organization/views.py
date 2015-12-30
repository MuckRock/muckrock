"""
Views for the organization application
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

import actstream
import datetime
import logging
import stripe

from muckrock.foia.models import FOIARequest
from muckrock.organization.models import Organization
from muckrock.organization.forms import CreateForm, \
                                        StaffCreateForm, \
                                        UpdateForm, \
                                        StaffUpdateForm, \
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
    It behaves differently if the current user is staff.
    """
    template_name = 'organization/create.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """
        A user must be logged in to create an organization.
        They cannot own any other orgs.
        Staff are exempt from the "can only own one" rule because
        they will likely be creating orgs for other folks.
        """
        already_owns_org = Organization.objects.filter(owner=self.request.user).exists()
        already_member = self.request.user.profile.organization is not None
        if (already_member or already_owns_org) and not self.request.user.is_staff:
            messages.error(self.request, 'You may only own one organization at a time.')
            return redirect('org-index')
        return super(OrganizationCreateView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        """Returns staff-specific form if user is staff."""
        form_class = CreateForm
        if self.request.user.is_staff:
            form_class = StaffCreateForm
        return form_class

    def get_success_url(self):
        """The success url is the organization activation page."""
        if not self.object:
            raise AttributeError('No organization created! Something went wrong.')
        success_url = reverse('org-activate', kwargs={'slug': self.object.slug})
        return success_url

    def form_valid(self, form):
        """
        When form is valid, save it.
        If the user is not staff, make the current user the owner.
        Finally, redirect to the organization's activation page.
        """
        # pylint:disable=attribute-defined-outside-init
        # pylint disabled because parent object does the same exact thing so its ok
        user = self.request.user
        organization = form.save(commit=False)
        if not user.is_staff:
            organization.owner = user
        organization.save()
        self.object = organization
        # redirect to the success url with a nice message
        logging.info('%s created %s', user, organization)
        messages.success(self.request, 'The organization has been created. Excellent!')
        return redirect(self.get_success_url())


class OrganizationActivateView(UpdateView):
    """Organization activation view"""
    model = Organization
    template_name = "organization/activate.html"
    form_class = UpdateForm

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """
        A user must be logged in to activate an organization.
        The user must be staff or the owner.
        The organization cannot already be active.
        """
        organization = self.get_object()
        user = self.request.user
        if not user.is_staff and not organization.is_owned_by(user):
            messages.error(self.request, 'You cannot activate an organization you do not own.')
            return redirect(organization.get_absolute_url())
        if organization.active:
            messages.error(self.request, 'You cannot activate an already active organization.')
            return redirect(organization.get_absolute_url())
        return super(OrganizationActivateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Adds Stripe pk and user's email to activation form."""
        context = super(OrganizationActivateView, self).get_context_data(**kwargs)
        organization = self.get_object()
        context['org'] = organization
        context['base_users'] = organization.max_users
        context['base_requests'] = organization.monthly_requests
        context['base_price'] = organization.monthly_cost/100.00
        context['user_email'] = self.request.user.email
        context['stripe_pk'] = STRIPE_PUB_KEY
        return context

    def form_valid(self, form):
        """When the form is valid, activate the organization."""
        # should expect a token from Stripe
        token = self.request.POST.get('stripe_token')
        organization = self.get_object()
        # Do not save the form! The activate_subscription method needs to compare the
        # new number of seats to the existing number of seats. If the UpdateForm is saved,
        # it will automatically save the new number of seats to the model since it is a ModelForm.
        num_seats = form.cleaned_data['max_users']
        an_error = False
        if token:
            try:
                organization.activate_subscription(token, num_seats)
                messages.success(self.request, 'Your organization subscription is active.')
                logging.info('%s activated %s', self.request.user, organization)
            except (AttributeError, ValueError) as exception:
                messages.error(self.request, exception)
                an_error = True
            except stripe.CardError as exception:
                messages.error(self.request, exception)
                an_error = True
            except (stripe.AuthenticationError, stripe.InvalidRequestError, stripe.StripeError):
                messages.error(self.request, 'Payment error. Your card has not been charged.')
                an_error = True
        else:
            messages.error(self.request, 'No payment information provided!')
            an_error = True
        if an_error:
            return self.form_invalid(form)
        else:
            return redirect(self.get_success_url())


class OrganizationUpdateView(UpdateView):
    """
    Presents a form for updating the organization.
    Behaves differently depending on whether the user is staff or the organization's owner.
    """
    model = Organization
    template_name = "organization/update.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """
        A user must be logged in to update an organization.
        The user must be staff or the owner.
        The organization cannot be inactive.
        """
        organization = self.get_object()
        user = self.request.user
        if not user.is_staff and not organization.is_owned_by(user):
            messages.error(self.request, 'You cannot update an organization you do not own.')
            return redirect(organization.get_absolute_url())
        if not organization.active:
            messages.error(self.request, 'You cannot update an inactive organization.')
            return redirect(organization.get_absolute_url())
        return super(OrganizationUpdateView, self).dispatch(*args, **kwargs)

    def get_form_class(self):
        """Returns a basic form for owners and a comprehensive form for staff."""
        form_class = UpdateForm
        if self.request.user.is_staff:
            form_class = StaffUpdateForm
        return form_class

    def get_context_data(self, **kwargs):
        """Adds Stripe pk and user's email to activation form."""
        context = super(OrganizationUpdateView, self).get_context_data(**kwargs)
        organization = self.get_object()
        context['org'] = organization
        context['base_users'] = organization.max_users
        context['base_requests'] = organization.monthly_requests
        context['base_price'] = organization.monthly_cost/100.00
        return context

    def form_valid(self, form):
        """Should handle a valid form differently depending on whether the user is staff."""
        organization = self.get_object()
        user = self.request.user
        max_users = form.cleaned_data['max_users']
        if user.is_staff:
            # if staff we want the changes made to the org to be saved before updating
            organization = form.save()
        organization.update_subscription(max_users)
        return redirect(self.get_success_url())

def deactivate_organization(request, slug):
    """Unsubscribes its owner from the recurring payment plan."""
    organization = get_object_or_404(Organization, slug=slug)
    # check if the user has the authority
    if not organization.is_owned_by(request.user) and not request.user.is_staff:
        messages.error(request, 'Only this organization\'s owner may deactivate it.')
        return redirect(organization)
    # check if org is already inactive
    if not organization.active:
        messages.error(request, 'This organization is already inactive.')
        return redirect(organization)
    # finally, actually deactivate the organization
    if request.method == 'POST':
        organization.cancel_subscription()
    return redirect(organization)


class OrganizationDeleteView(DeleteView):
    """
    Only staff or the org owner may delete the organization.
    The org may only be deleted when inactive.
    """
    model = Organization
    template_name = "organization/delete.html"
    success_url = '/organization/'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        """
        A user must be logged in to delete an organization.
        The user must be staff or the owner.
        The organization cannot be active.
        """
        organization = self.get_object()
        user = self.request.user
        if not user.is_staff and not organization.is_owned_by(user):
            messages.error(self.request, 'You cannot delete an organization you do not own.')
            return redirect(organization.get_absolute_url())
        if organization.active:
            messages.error(self.request, 'You cannot delete an active organization.')
            return redirect(organization.get_absolute_url())
        return super(OrganizationDeleteView, self).dispatch(*args, **kwargs)


class OrganizationDetailView(DetailView):
    """Organization detail view"""
    model = Organization
    template_name = "organization/detail.html"

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(OrganizationDetailView, self).get_context_data(**kwargs)
        organization = context['organization']
        context['is_staff'] = False
        context['is_owner'] = False
        context['is_member'] = False
        user = self.request.user
        if user.is_authenticated():
            context['is_staff'] = user.is_staff
            context['is_owner'] = organization.is_owned_by(user)
            context['is_member'] = user.profile.is_member_of(organization)
        context['requests'] = FOIARequest.objects.organization(organization).get_viewable(user)[:99]
        context['members'] = organization.members.select_related('user').all()
        context['available'] = {
            'requests': organization.num_requests,
            'seats': organization.max_users - organization.members.count()
        }
        context['progress'] = {
            'requests': ((1.0*organization.num_requests)/organization.monthly_requests)*100,
            'seats': (1.0-(1.0*organization.members.count())/organization.max_users)*100
        }
        try:
            date_update = organization.date_update
            refresh_date = datetime.date(date_update.year, date_update.month + 1, 1)
        except ValueError:
            # ValueError should happen if the current month is December
            refresh_date = datetime.date(date_update.year + 1, 1, 1)
        context['refresh_date'] = refresh_date
        context['add_members_form'] = AddMembersForm()
        context['sidebar_admin_url'] = reverse(
            'admin:organization_organization_change',
            args=(organization.pk,))
        return context

    def post(self, request, **kwargs):
        """Handle form submission for adding and removing users"""
        # pylint: disable=attribute-defined-outside-init
        # disable setting self.object because its actually ok and Django does this also
        self.object = self.get_object()
        action = request.POST.get('action', '')
        if action == 'add_members':
            self.add_members(request)
        elif action == 'remove_member':
            self.remove_member(request)
        else:
            messages.error(request, 'This action is not available.')
        context = self.get_context_data()
        return self.render_to_response(context)

    def add_members(self, request):
        """Grants organization membership to a list of users"""
        organization = self.get_object()
        if not organization.is_owned_by(request.user) and not request.user.is_staff:
            messages.error(request, 'You cannot add members this organization.')
            return
        form = AddMembersForm(request.POST)
        if form.is_valid():
            new_members = form.cleaned_data['members']
            new_member_count = len(new_members)
            existing_member_count = organization.members.count()
            if new_member_count + existing_member_count > organization.max_users:
                difference = (new_member_count + existing_member_count) - organization.max_users
                seat = 'seats' if difference > 1 else 'seat'
                messages.error(request, 'You will need to purchase %d %s.' % (difference, seat))
                return
            if not organization.active:
                messages.error(request, 'You may not add members to an inactive organization.')
                return
            members_added = 0
            for member in new_members:
                try:
                    if organization.add_member(member):
                        actstream.action.send(
                            request.user,
                            verb='added',
                            action_object=member,
                            target=organization
                        )
                        logging.info('%s %s %s to %s.',
                            request.user,
                            'added',
                            member,
                            organization
                        )
                        members_added += 1
                except AttributeError as exception:
                    messages.error(request, exception)
            if members_added > 0:
                members_plural = 'members' if members_added > 1 else 'member'
                messages.success(request, 'You added %d %s.' % (members_added, members_plural))
        return

    def remove_member(self, request):
        """Removes a single member from an organization"""
        organization = self.get_object()
        try:
            user_pk = request.POST['member']
            user = User.objects.select_related('profile').get(pk=user_pk)
        except (KeyError, User.DoesNotExist):
            messages.error(request, 'No member selected to remove.')
            return
        # let members remove themselves from the organization, but nobody else
        removing_self = user == request.user
        user_is_owner = organization.owner == request.user
        if removing_self or user_is_owner or request.user.is_staff:
            if organization.remove_member(user):
                actstream.action.send(
                    request.user,
                    verb='removed',
                    action_object=user,
                    target=organization
                )
                logging.info('%s %s %s from %s.', request.user, 'removed', user, organization)
                if removing_self:
                    msg = 'You are no longer a member.'
                else:
                    msg = 'You removed membership from %s.' % user.first_name
                messages.success(request, msg)
        else:
            messages.error(request, 'You do not have permission to remove this member.')
        return
