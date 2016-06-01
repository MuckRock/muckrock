"""
Views for the accounts application
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import (
        HttpResponse,
        HttpResponseBadRequest,
        HttpResponseNotAllowed,
        HttpResponseRedirect,
        )
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView

from datetime import date
from rest_framework import viewsets
from rest_framework.permissions import (
        DjangoModelPermissions,
        DjangoModelPermissionsOrAnonReadOnly,
        )
import json
import logging
import stripe
import sys

from muckrock.accounts.forms import (
        ProfileSettingsForm,
        EmailSettingsForm,
        BillingPreferencesForm,
        RegisterForm,
        RegisterOrganizationForm,
        RegistrationCompletionForm
        )
from muckrock.accounts.models import Profile, Statistics, ACCT_TYPES
from muckrock.accounts.serializers import UserSerializer, StatisticsSerializer
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.organization.models import Organization
from muckrock.project.models import Project
from muckrock.message.tasks import (
        send_charge_receipt,
        send_invoice_receipt,
        failed_payment,
        email_verify,
        welcome,
        gift,
        )
from muckrock.views import MRFilterableListView

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_new_user(request, valid_form):
    """Create a user from the valid form, give them a profile, and log them in."""
    new_user = valid_form.save()
    Profile.objects.create(
        user=new_user,
        acct_type='basic',
        monthly_requests=0,
        date_update=date.today()
    )
    new_user = authenticate(
        username=valid_form.cleaned_data['username'],
        password=valid_form.cleaned_data['password1']
    )
    login(request, new_user)
    return new_user

def account_logout(request):
    """Logs a user out of their account and redirects to index page"""
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('index')


class SignupView(FormView):
    """Generic ancestor for all account signup views."""
    def dispatch(self, *args, **kwargs):
        """Prevent logged-in users from accessing this view."""
        if self.request.user.is_authenticated():
            return HttpResponseRedirect(self.get_success_url())
        return super(SignupView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        """Allows the success URL to be overridden by a query parameter."""
        url_redirect = self.request.GET.get('next', None)
        return url_redirect if url_redirect else reverse('acct-my-profile')


class BasicSignupView(SignupView):
    """Allows a logged-out user to register for a basic account."""
    template_name = 'accounts/signup/basic.html'
    form_class = RegisterForm

    def form_valid(self, form):
        """When form is valid, create the user."""
        new_user = create_new_user(self.request, form)
        welcome.delay(new_user)
        success_msg = 'Your account was successfully created. Welcome to MuckRock!'
        messages.success(self.request, success_msg)
        return super(BasicSignupView, self).form_valid(form)


class ProfessionalSignupView(SignupView):
    """Allows a logged-out user to register for a professional account."""
    template_name = 'accounts/signup/professional.html'
    form_class = RegisterForm

    def get_context_data(self, **kwargs):
        """Adds Stripe PK to template context data."""
        context = super(ProfessionalSignupView, self).get_context_data(**kwargs)
        context['stripe_pk'] = settings.STRIPE_PUB_KEY
        return context

    def form_valid(self, form):
        """When form is valid, create the user and begin their professional subscription."""
        new_user = create_new_user(self.request, form)
        welcome.delay(new_user)
        try:
            new_user.profile.start_pro_subscription(self.request.POST['stripe_token'])
            success_msg = 'Your professional account was successfully created. Welcome to MuckRock!'
            messages.success(self.request, success_msg)
        except KeyError:
            # no payment information provided
            error_msg = ('Your account was successfully created, '
                         'but you did not provide payment information. '
                         'You can subscribe from the account management page.')
            messages.error(self.request, error_msg)
        except stripe.error.CardError:
            # card declined
            error_msg = ('Your account was successfully created, but your card was declined. '
                         'You can subscribe from the account management page.')
            messages.error(self.request, error_msg)
        except (stripe.error.InvalidRequestError, stripe.error.APIError):
            # invalid request made to stripe
            error_msg = ('Your account was successfully created, '
                         'but we could not contact our payment provider. '
                         'You can subscribe from the account management page.')
            messages.error(self.request, error_msg)
        return super(ProfessionalSignupView, self).form_valid(form)


class OrganizationSignupView(SignupView):
    """Allows a logged-out user to register for an account and an organization."""
    template_name = 'accounts/signup/organization.html'
    form_class = RegisterOrganizationForm

    def form_valid(self, form):
        """
        When form is valid, create the user and the organization.
        Then redirect to the organization activation page.
        """
        new_user = create_new_user(self.request, form)
        new_org = form.create_organization(new_user)
        welcome.delay(new_user)
        messages.success(self.request, 'Your account and organization were successfully created.')
        return HttpResponseRedirect(reverse('org-activate', kwargs={'slug': new_org.slug}))


class AccountsView(TemplateView):
    """
    Displays the list of payment plans.
    If user is logged out, it lets them register for any plan.
    If user is logged in, it lets them up- or downgrade their account to any plan.
    """
    template_name = 'accounts/plans.html'

    def get_context_data(self, **kwargs):
        """Returns a context based on whether the user is logged in or logged out."""
        context = super(AccountsView, self).get_context_data(**kwargs)
        logged_in = self.request.user.is_authenticated()
        if logged_in:
            context['acct_type'] = self.request.user.profile.acct_type
            context['email'] = self.request.user.email
            try:
                context['org'] = Organization.objects.get(owner=self.request.user)
            except Organization.DoesNotExist:
                context['org'] = None
        context['stripe_pk'] = settings.STRIPE_PUB_KEY
        context['logged_in'] = logged_in
        return context

    def post(self, request, **kwargs):
        """Handle upgrades and downgrades of accounts"""
        try:
            action = request.POST['action']
            account_actions = {
                'downgrade': downgrade,
                'upgrade': upgrade
            }
            account_actions[action](request)
        except KeyError as exception:
            logger.error(exception)
            messages.error(request, 'No available action was specified.')
        except AttributeError as exception:
            logger.error(exception)
            error_msg = 'You cannot be logged out and modify your account.'
            messages.error(request, error_msg)
        except ValueError as exception:
            logger.error(exception)
            messages.error(request, exception)
        return self.render_to_response(self.get_context_data())

def upgrade(request):
    """Upgrades the user from a Basic to a Professional account."""
    if not request.user.is_authenticated():
        raise AttributeError('Cannot upgrade an anonymous user.')
    is_pro_user = request.user.profile.acct_type in ['pro', 'proxy']
    is_org_owner = Organization.objects.filter(owner=request.user).exists()
    if is_pro_user:
        raise ValueError('Cannot upgrade this account, it is already Professional.')
    if is_org_owner:
        raise ValueError('Cannot upgrade this account, it owns an organization.')
    token = request.POST.get('stripe_token')
    if not token:
        raise ValueError('Cannot upgrade this account, no Stripe token provided.')
    request.user.profile.start_pro_subscription(token)

def downgrade(request):
    """Downgrades the user from a Professional to a Basic account."""
    if not request.user.is_authenticated():
        raise AttributeError('Cannot downgrade an anonymous user.')
    if request.user.profile.acct_type != 'pro':
        raise ValueError('Cannot downgrade this account, it is not Professional.')
    request.user.profile.cancel_pro_subscription()

@login_required
def profile_settings(request):
    """Update a users information"""
    user_profile = request.user.profile
    settings_forms = {
        'profile': ProfileSettingsForm,
        'email': EmailSettingsForm,
        'billing': BillingPreferencesForm
    }
    if request.method == 'POST':
        action = request.POST.get('action')
        if action:
            form = settings_forms[action]
            form = form(request.POST, request.FILES, instance=user_profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your settings have been updated.')
    profile_initial = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    }
    email_initial = {
        'email': request.user.email
    }
    profile_form = ProfileSettingsForm(initial=profile_initial, instance=user_profile)
    email_form = EmailSettingsForm(initial=email_initial, instance=user_profile)
    current_plan = dict(ACCT_TYPES)[user_profile.acct_type]
    context = {
        'stripe_pk': settings.STRIPE_PUB_KEY,
        'profile_form': profile_form,
        'email_form': email_form,
        'current_plan': current_plan,
        'credit_card': user_profile.card()
    }
    return render_to_response(
        'accounts/settings.html',
        context,
        context_instance=RequestContext(request))

def buy_requests(request, username=None):
    """A purchaser buys requests for a recipient. The recipient can even be themselves!"""
    url_redirect = request.GET.get('next', 'acct-my-profile')
    recipient = get_object_or_404(User, username=username)
    purchaser = request.user
    request_price = 2000
    if purchaser.is_authenticated():
        request_count = purchaser.profile.bundled_requests()
    else:
        request_count = 4
    try:
        if request.POST:
            stripe_token = request.POST.get('stripe_token')
            stripe_email = request.POST.get('stripe_email')
            if not stripe_token and not stripe_email:
                raise KeyError('Missing Stripe payment data.')
            # take from the purchaser
            stripe.Charge.create(
                amount=request_price,
                currency='usd',
                source=stripe_token,
                metadata={
                    'email': stripe_email,
                    'action': 'request-purchase',
                }
            )
            # and give to the recipient
            recipient.profile.num_requests += request_count
            recipient.profile.save()
            # record the purchase
            request.session['ga'] = 'request_purchase'
            msg = 'Purchase successful. '
            if recipient == purchaser:
                msg += '%d requests have been added to your account.' % request_count
            else:
                msg += '%d requests have been gifted to %s' % (request_count, recipient.first_name)
                gift_description = '%d requests' % request_count
                # notify the recipient with an email
                gift.delay(recipient, purchaser, gift_description)
            messages.success(request, msg)
            logger.info('%s purchased %d requests', purchaser.username, request_count)
    except KeyError as exception:
        msg = 'Payment error: %s' % exception
        messages.error(request, msg)
        logger.warn('Payment error: %s', exception, exc_info=sys.exc_info())
    except stripe.CardError as exception:
        msg = 'Payment error: %s Your card has not been charged.' % exception
        messages.error(request, msg)
        logger.warn('Payment error: %s', exception, exc_info=sys.exc_info())
    return redirect(url_redirect)

@login_required
def verify_email(request):
    """Verifies a user's email address"""
    user = request.user
    _profile = user.profile
    key = request.GET.get('key')
    if not _profile.email_confirmed:
        if key:
            if key == _profile.confirmation_key:
                _profile.email_confirmed = True
                _profile.save()
                messages.success(request, 'Your email address has been confirmed.')
            else:
                messages.error(request, 'Your confirmation key is invalid.')
        else:
            email_verify.delay(user)
            messages.info(request, 'We just sent you an email containing your verification link.')
    else:
        messages.warning(request, 'Your email is already confirmed, no need to verify again!')
    return redirect(_profile)

def profile(request, username=None):
    """View a user's profile"""
    if username is None:
        if request.user.is_anonymous():
            return redirect('acct-login')
        else:
            return redirect('acct-profile', username=request.user.username)
    user = get_object_or_404(User, username=username)
    user_profile = user.profile
    org = user_profile.organization
    requests = (FOIARequest.objects
            .filter(user=user)
            .get_viewable(request.user)
            .select_related(
                'jurisdiction',
                'jurisdiction__parent',
                'jurisdiction__parent__parent',
                ))
    recent_requests = requests.order_by('-date_submitted')[:5]
    recent_completed = requests.filter(status='done').order_by('-date_done')[:5]
    articles = Article.objects.get_published().filter(authors=user)[:5]
    projects = Project.objects.get_for_contributor(user).get_visible(request.user)[:3]
    context = {
        'user_obj': user,
        'profile': user_profile,
        'org': org,
        'projects': projects,
        'recent_requests': recent_requests,
        'recent_completed': recent_completed,
        'articles': articles,
        'stripe_pk': settings.STRIPE_PUB_KEY,
        'sidebar_admin_url': reverse('admin:auth_user_change', args=(user.pk,)),
    }
    return render_to_response(
        'accounts/profile.html',
        context,
        context_instance=RequestContext(request)
    )

@csrf_exempt
def stripe_webhook(request):
    """Handle webhooks from stripe"""
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])
    try:
        event_json = json.loads(request.body)
        event_id = event_json['id']
        event_type = event_json['type']
        event_object_id = event_json['data']['object']['id']
    except (TypeError, ValueError, SyntaxError) as exception:
        logging.error('Error parsing JSON: %s', exception)
        return HttpResponseBadRequest()
    except KeyError as exception:
        logging.error('Unexpected dictionary structure: %s in %s', exception, event_json)
        return HttpResponseBadRequest()
    # If we've made it this far, then the webhook message was successfully sent!
    # Now it's up to us to act on it.'
    success_msg = (
        'Received Stripe webhook\n'
        '\tfrom:\t%(address)s\n'
        '\tid:\t%(id)s\n'
        '\ttype:\t%(type)s\n'
        '\tdata:\t%(data)s\n'
    ) % {
        'address': request.META['REMOTE_ADDR'],
        'id': event_id,
        'type': event_type,
        'data': event_json
    }
    logger.info(success_msg)
    if event_type == 'charge.succeeded':
        send_charge_receipt.delay(event_object_id)
    elif event_type == 'invoice.payment_succeeded':
        send_invoice_receipt.delay(event_object_id)
    elif event_type == 'invoice.payment_failed':
        failed_payment.delay(event_object_id)
    return HttpResponse()

@method_decorator(login_required, name='dispatch')
class RegistrationCompletionView(FormView):
    """Provides a form for a new user to change their username and password.
    Will verify their email if a key is provided."""
    template_name = 'forms/base_form.html'
    form_class = RegistrationCompletionForm

    def get_initial(self):
        """Adds the username as an initial value."""
        return {'username': self.request.user.username}

    def get_form_kwargs(self):
        """Adds the user to the form kwargs."""
        kwargs = super(RegistrationCompletionView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        if 'key' in request.GET:
            key = request.GET['key']
            if key == profile.confirmation_key:
                profile.email_confirmed = True
                profile.save()
                messages.success(request, 'Your email is validated.')
        return super(RegistrationCompletionView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        """Saves the form and redirects to the success url."""
        form.save(commit=True)
        messages.success(self.request, 'Your account is now complete.')
        return redirect(self.get_success_url())

    def get_success_url(self):
        """Return the user's profile."""
        return reverse('acct-profile', kwargs={'username': self.request.user.username})


class UserViewSet(viewsets.ModelViewSet):
    """API views for User"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = User.objects.prefetch_related('profile', 'groups')
    serializer_class = UserSerializer
    permission_classes = (DjangoModelPermissions,)
    filter_fields = ('username', 'first_name', 'last_name', 'email', 'is_staff')


class StatisticsViewSet(viewsets.ModelViewSet):
    """API views for Statistics"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Statistics.objects.all()
    serializer_class = StatisticsSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    filter_fields = ('date',)


class ProxyList(MRFilterableListView):
    """List of Proxies"""
    model = User
    title = 'Proxies'
    template_name = 'lists/proxy_list.html'
    default_sort = 'profile__state'

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Staff only"""
        return super(ProxyList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Display all proxies"""
        objects = super(ProxyList, self).get_queryset()
        return (objects
                .filter(profile__acct_type='proxy')
                .select_related('profile'))
