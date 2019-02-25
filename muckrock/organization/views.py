"""
Views for the organization application
"""
# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView

# Standard Library
import datetime
import logging

# Third Party
import stripe

# MuckRock
from muckrock.accounts.utils import mixpanel_event
from muckrock.core.utils import new_action
from muckrock.core.views import MROrderedListView
from muckrock.foia.models import FOIARequest
from muckrock.organization.forms import (
    AddMembersForm,
    CreateForm,
    StaffCreateForm,
    StaffUpdateForm,
    UpdateForm,
)
from muckrock.organization.models import Organization


class OrganizationListView(MROrderedListView):
    """List of organizations"""
    model = Organization
    template_name = "organization/list.html"
    sort_map = {
        'name': 'name',
        'owner': 'owner__username',
    }

    def get_queryset(self):
        """Filter out private orgs for non-staff"""
        queryset = (
            super(OrganizationListView, self).get_queryset()
            .select_related('owner')
        )
        if not self.request.user.is_staff:
            queryset = queryset.filter(private=False)
        return queryset


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
        already_owns_org = Organization.objects.filter(owner=self.request.user
                                                       ).exists()
        already_member = self.request.user.profile.organization is not None
        if (
            already_member or already_owns_org
        ) and not self.request.user.is_staff:
            messages.error(
                self.request, 'You may only own one organization at a time.'
            )
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
            raise AttributeError(
                'No organization created! Something went wrong.'
            )
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
        if not user.profile.organization:
            user.profile.organization = organization
            user.profile.save()
        self.object = organization
        # redirect to the success url with a nice message
        logging.info('%s created %s', user, organization)
        messages.success(
            self.request, 'The organization has been created. Excellent!'
        )
        mixpanel_event(
            self.request,
            'Organization Created',
            organization.mixpanel_event(),
        )
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
            messages.error(
                self.request,
                'You cannot activate an organization you do not own.'
            )
            return redirect(organization.get_absolute_url())
        if organization.active:
            messages.error(
                self.request,
                'You cannot activate an already active organization.'
            )
            return redirect(organization.get_absolute_url())
        return super(OrganizationActivateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Adds Stripe pk and user's email to activation form."""
        context = super(OrganizationActivateView,
                        self).get_context_data(**kwargs)
        organization = context['object']
        context['org'] = organization
        context['base_users'] = organization.max_users
        context['base_requests'] = organization.monthly_requests
        context['base_price'] = organization.monthly_cost / 100.00
        context['user_email'] = self.request.user.email
        context['stripe_pk'] = settings.STRIPE_PUB_KEY
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
                messages.success(
                    self.request, 'Your organization subscription is active.'
                )
                logging.info('%s activated %s', self.request.user, organization)
                mixpanel_event(
                    self.request,
                    'Organization Activated',
                    organization.mixpanel_event(),
                )
            except (AttributeError, ValueError) as exception:
                messages.error(self.request, exception)
                an_error = True
            except stripe.CardError as exception:
                messages.error(self.request, exception)
                an_error = True
            except (
                stripe.AuthenticationError, stripe.InvalidRequestError,
                stripe.StripeError
            ):
                messages.error(
                    self.request,
                    'Payment error. Your card has not been charged.'
                )
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
            messages.error(
                self.request,
                'You cannot update an organization you do not own.'
            )
            return redirect(organization.get_absolute_url())
        if not organization.active:
            messages.error(
                self.request, 'You cannot update an inactive organization.'
            )
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
        organization = context['object']
        context['org'] = organization
        context['base_users'] = organization.max_users
        context['base_requests'] = organization.monthly_requests
        context['base_price'] = organization.monthly_cost / 100.00
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
        mixpanel_event(
            self.request,
            'Organization Updated',
            organization.mixpanel_event(),
        )
        return redirect(self.get_success_url())


def deactivate_organization(request, slug):
    """Unsubscribes its owner from the recurring payment plan."""
    organization = get_object_or_404(Organization, slug=slug)
    # check if the user has the authority
    if not organization.is_owned_by(request.user) and not request.user.is_staff:
        messages.error(
            request, 'Only this organization\'s owner may deactivate it.'
        )
        return redirect(organization)
    # check if org is already inactive
    if not organization.active:
        messages.error(request, 'This organization is already inactive.')
        return redirect(organization)
    # finally, actually deactivate the organization
    if request.method == 'POST':
        organization.cancel_subscription()
        mixpanel_event(
            request,
            'Organization Deactivated',
            organization.mixpanel_event(),
        )
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
            messages.error(
                self.request,
                'You cannot delete an organization you do not own.'
            )
            return redirect(organization.get_absolute_url())
        if organization.active:
            messages.error(
                self.request, 'You cannot delete an active organization.'
            )
            return redirect(organization.get_absolute_url())
        mixpanel_event(
            self.request,
            'Organization Deleted',
            organization.mixpanel_event(),
        )
        return super(OrganizationDeleteView, self).dispatch(*args, **kwargs)


class OrganizationDetailView(DetailView):
    """Organization detail view"""
    queryset = Organization.objects.select_related('owner')
    template_name = "organization/detail.html"

    def get_object(self, queryset=None):
        """Get the org"""
        org = super(OrganizationDetailView, self).get_object(queryset=queryset)
        user = self.request.user
        is_member = user.is_authenticated() and user.profile.is_member_of(org)
        if org.private and not is_member and not user.is_staff:
            raise Http404
        return org

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
        requests = (
            FOIARequest.objects.organization(organization).get_viewable(user)
        )
        context['requests'] = {
            'count': requests.count(),
            'filed': requests.order_by('-composer__datetime_submitted')[:10],
            'completed': requests.get_done().order_by('-datetime_done')[:10]
        }

        context['members'
                ] = organization.members.select_related('user__profile')
        num_requests = organization.get_requests()
        context['available'] = {
            'requests': num_requests,
            'seats': organization.max_users - len(context['members'])
        }
        context['progress'] = {}
        if organization.monthly_requests > 0:
            context['progress']['requests'] = (
                float(num_requests) / organization.monthly_requests
            ) * 100
        else:
            context['progress']['requests'] = 0
        if organization.max_users > 0:
            context['progress']['seats'] = (
                1.0 - float(len(context['members'])) / organization.max_users
            ) * 100
        else:
            context['progress']['seats'] = 0

        try:
            date_update = organization.date_update
            refresh_date = datetime.date(
                date_update.year, date_update.month + 1, 1
            )
        except ValueError:
            # ValueError should happen if the current month is December
            refresh_date = datetime.date(date_update.year + 1, 1, 1)
        context['refresh_date'] = refresh_date
        context['add_members_form'] = AddMembersForm()
        context['sidebar_admin_url'] = reverse(
            'admin:organization_organization_change', args=(organization.pk,)
        )
        return context

    def post(self, request, **kwargs):
        """Handle form submission for adding and removing users"""
        org = self.get_object()
        action = request.POST.get('action', '')
        is_owner = org.is_owned_by(self.request.user)
        is_owner_or_staff = is_owner or self.request.user.is_staff
        if action == 'add_members':
            self.add_members(request)
        elif action == 'remove_member':
            self.remove_member(request)
        elif action == 'private' and is_owner_or_staff:
            org.private = True
            org.save()
            messages.success(request, 'Organization has been made private')
        elif action == 'public' and is_owner_or_staff:
            org.private = False
            org.save()
            messages.success(request, 'Organization has been made public')
        else:
            messages.error(request, 'This action is not available.')
        return redirect(org)

    def add_members(self, request):
        """Grants organization membership to a list of users"""
        organization = self.get_object()
        if not organization.is_owned_by(
            request.user
        ) and not request.user.is_staff:
            messages.error(request, 'You cannot add members this organization.')
            return
        form = AddMembersForm(request.POST)
        if form.is_valid():
            new_members = form.cleaned_data['members']
            new_member_count = len(new_members)
            existing_member_count = organization.members.count()
            if new_member_count + existing_member_count > organization.max_users:
                difference = (
                    new_member_count + existing_member_count
                ) - organization.max_users
                seat = 'seats' if difference > 1 else 'seat'
                messages.error(
                    request,
                    'You will need to purchase %d %s.' % (difference, seat)
                )
                return
            if not organization.active:
                messages.error(
                    request,
                    'You may not add members to an inactive organization.'
                )
                return
            members_added = 0
            for member in new_members:
                try:
                    if organization.add_member(member):
                        new_action(
                            request.user,
                            'added',
                            action_object=member,
                            target=organization
                        )
                        logging.info(
                            '%s %s %s to %s.', request.user, 'added', member,
                            organization
                        )
                        members_added += 1
                except AttributeError as exception:
                    messages.error(request, exception)
            if members_added > 0:
                members_plural = 'members' if members_added > 1 else 'member'
                messages.success(
                    request,
                    'You added %d %s.' % (members_added, members_plural)
                )
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
                new_action(
                    request.user,
                    'removed',
                    action_object=user,
                    target=organization
                )
                logging.info(
                    '%s %s %s from %s.', request.user, 'removed', user,
                    organization
                )
                if removing_self:
                    msg = 'You are no longer a member.'
                else:
                    msg = 'You removed membership from %s.' % user.profile.full_name
                messages.success(request, msg)
        else:
            messages.error(
                request, 'You do not have permission to remove this member.'
            )
        return
