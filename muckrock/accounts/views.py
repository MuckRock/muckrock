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
from django.shortcuts import (
        get_object_or_404,
        redirect,
        render,
        )
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView, ListView

from datetime import date
from rest_framework import viewsets
from rest_framework.permissions import (
        DjangoModelPermissionsOrAnonReadOnly,
        IsAdminUser,
        )
import json
import logging
import stripe
import sys

from muckrock.accounts.filters import ProxyFilterSet
from muckrock.accounts.forms import (
        ProfileSettingsForm,
        EmailSettingsForm,
        BillingPreferencesForm,
        OrgPreferencesForm,
        ReceiptForm,
        RegisterForm,
        RegisterOrganizationForm,
        RegistrationCompletionForm
        )
from muckrock.accounts.models import (
        Profile,
        Notification,
        Statistics,
        ReceiptEmail,
        ACCT_TYPES,
        )
from muckrock.accounts.serializers import UserSerializer, StatisticsSerializer
from muckrock.accounts.utils import validate_stripe_email
from muckrock.agency.models import Agency
from muckrcok.communication.models import EmailAddress
from muckrock.foia.models import FOIARequest
from muckrock.message.email import TemplateEmail
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
from muckrock.views import MRFilterListView
from muckrock.utils import stripe_retry_on_error

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
        except (KeyError, AttributeError):
            # no payment information provided
            logger.warn('No payment information provided.')
            error_msg = ('Your account was successfully created, '
                         'but you did not provide payment information. '
                         'You can subscribe from the account management page.')
            messages.error(self.request, error_msg)
        except stripe.error.CardError:
            # card declined
            logger.warn('Card was declined.')
            error_msg = ('Your account was successfully created, but your card was declined. '
                         'You can subscribe from the account management page.')
            messages.error(self.request, error_msg)
        except (stripe.error.InvalidRequestError, stripe.error.APIError):
            # invalid request made to stripe
            logger.warn('No payment information provided.')
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
            context['org'] = (Organization.objects
                    .filter(owner=self.request.user)
                    .first())
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
        except stripe.error.CardError:
            # card declined
            logger.warn('Card was declined.')
            messages.error(request, 'Your card was declined')
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
    # pylint: disable=too-many-locals
    user_profile = request.user.profile
    settings_forms = {
        'profile': ProfileSettingsForm,
        'email': EmailSettingsForm,
        'billing': BillingPreferencesForm,
        'org': OrgPreferencesForm,
    }
    receipt_form = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'receipt':
            receipt_form = ReceiptForm(request.POST)
            if receipt_form.is_valid():
                new_emails = receipt_form.cleaned_data['emails'].split('\n')
                new_emails = {e.strip() for e in new_emails}
                old_emails = {r.email for r in
                        request.user.receipt_emails.all()}
                ReceiptEmail.objects.filter(
                        user=request.user,
                        email__in=(old_emails - new_emails),
                        ).delete()
                ReceiptEmail.objects.bulk_create(
                        [ReceiptEmail(user=request.user, email=e)
                            for e in new_emails - old_emails])
                messages.success(request, 'Your settings have been updated.')
                return redirect('acct-settings')
        elif action:
            form = settings_forms[action]
            form = form(request.POST, request.FILES, instance=user_profile)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your settings have been updated.')
                return redirect('acct-settings')
    profile_initial = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    }
    email_initial = {
        'email': request.user.email
    }
    receipt_initial = {
        'emails': '\n'.join(r.email for r in request.user.receipt_emails.all())
        }
    profile_form = ProfileSettingsForm(initial=profile_initial, instance=user_profile)
    email_form = EmailSettingsForm(initial=email_initial, instance=user_profile)
    org_form = OrgPreferencesForm(instance=user_profile)
    receipt_form = receipt_form or ReceiptForm(initial=receipt_initial)
    current_plan = dict(ACCT_TYPES)[user_profile.acct_type]
    context = {
        'stripe_pk': settings.STRIPE_PUB_KEY,
        'profile_form': profile_form,
        'email_form': email_form,
        'receipt_form': receipt_form,
        'org_form': org_form,
        'current_plan': current_plan,
        'credit_card': user_profile.card()
    }
    return render(
            request,
            'accounts/settings.html',
            context,
            )

def buy_requests(request, username=None):
    """A purchaser buys requests for a recipient. The recipient can even be themselves!"""
    url_redirect = request.GET.get('next', 'acct-my-profile')
    bundles = int(request.POST.get('bundles', 1))
    recipient = get_object_or_404(User, username=username)
    purchaser = request.user
    request_price = bundles * 2000
    if purchaser.is_authenticated():
        request_count = bundles * purchaser.profile.bundled_requests()
    else:
        request_count = bundles * 4
    try:
        if request.POST:
            stripe_token = request.POST.get('stripe_token')
            stripe_email = request.POST.get('stripe_email')
            stripe_email = validate_stripe_email(stripe_email)
            if not stripe_token or not stripe_email:
                raise KeyError('Missing Stripe payment data.')
            # take from the purchaser
            stripe_retry_on_error(
                    stripe.Charge.create,
                    amount=request_price,
                    currency='usd',
                    source=stripe_token,
                    metadata={
                        'email': stripe_email,
                        'action': 'request-purchase',
                        },
                    idempotency_key=True,
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
    except (stripe.error.InvalidRequestError, stripe.error.APIError) as exc:
        msg = 'Payment error: Your card has not been charged.'
        messages.error(request, msg)
        logger.warn('Payment error: %s', exc, exc_info=sys.exc_info())
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
    if (request.method == "POST" and
            request.user.is_staff and
            request.POST.get('action') == 'cancel-pro'):
        user.profile.cancel_pro_subscription()
        messages.success(request, 'Pro account has been cancelled')
        return redirect('acct-profile', username=username)
    user_profile = user.profile
    org = user_profile.organization
    show_org_link = (
            org and (
                not org.private or
                request.user.is_staff
                or (
                    request.user.is_authenticated() and
                    request.user.profile.is_member_of(org)
                    )))
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
        'show_org_link': show_org_link,
        'projects': projects,
        'requests': {
            'all': requests,
            'recent': recent_requests,
            'completed': recent_completed
        },
        'articles': articles,
        'stripe_pk': settings.STRIPE_PUB_KEY,
        'sidebar_admin_url': reverse('admin:auth_user_change', args=(user.pk,)),
    }
    return render(
            request,
            'accounts/profile.html',
            context,
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
        if event_type.startswith(('charge', 'invoice')):
            event_object_id = event_json['data']['object'].get('id', '')
        else:
            event_object_id = ''
    except (TypeError, ValueError, SyntaxError) as exception:
        logging.error('Error parsing JSON: %s', exception)
        return HttpResponseBadRequest()
    except KeyError as exception:
        logging.error('Unexpected dictionary structure: %s in %s', exception, event_json)
        return HttpResponseBadRequest()
    # If we've made it this far, then the webhook message was successfully sent!
    # Now it's up to us to act on it.
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
        _profile = request.user.profile
        if 'key' in request.GET:
            key = request.GET['key']
            if key == _profile.confirmation_key:
                _profile.email_confirmed = True
                _profile.save()
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
    queryset = (User.objects
            .order_by('id')
            .prefetch_related('profile', 'groups')
            )
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser,)
    filter_fields = ('username', 'first_name', 'last_name', 'email', 'is_staff')


class StatisticsViewSet(viewsets.ModelViewSet):
    """API views for Statistics"""
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-public-methods
    queryset = Statistics.objects.all()
    serializer_class = StatisticsSerializer
    permission_classes = (DjangoModelPermissionsOrAnonReadOnly,)
    filter_fields = ('date',)


@method_decorator(login_required, name='dispatch')
class NotificationList(ListView):
    """List of notifications for a user."""
    model = Notification
    template_name = 'accounts/notifications_all.html'
    context_object_name = 'notifications'
    title = 'All Notifications'

    def get_queryset(self):
        """Return all notifications for the user making the request."""
        user = self.request.user
        notifications = super(NotificationList, self).get_queryset()
        return notifications.for_user(user).order_by('-datetime')

    def get_paginate_by(self, queryset):
        """Paginates list by the return value"""
        try:
            per_page = int(self.request.GET.get('per_page'))
            return max(min(per_page, 100), 5)
        except (ValueError, TypeError):
            return 25

    def get_context_data(self, **kwargs):
        """Add the title to the context"""
        context = super(NotificationList, self).get_context_data(**kwargs)
        context['title'] = self.title
        return context

    def mark_all_read(self):
        """Mark all notifications for the view as read."""
        notifications = self.get_queryset()
        # to be more efficient, let's just get the unread ones
        notifications = notifications.get_unread()
        for notification in notifications:
            notification.mark_read()

    def post(self, request, *args, **kwargs):
        """Handle post actions to this view"""
        action = request.POST.get('action')
        if action == 'mark_all_read':
            self.mark_all_read()
        return self.get(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class UnreadNotificationList(NotificationList):
    """List only unread notifications for a user."""
    template_name = 'accounts/notifications_unread.html'
    title = 'Unread Notifications'

    def get_queryset(self):
        """Only return unread notifications."""
        notifications = super(UnreadNotificationList, self).get_queryset()
        return notifications.get_unread()


class ProxyList(MRFilterListView):
    """List of Proxies"""
    model = User
    filter_class = ProxyFilterSet
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


def agency_redirect_login(
        request, agency_slug, agency_idx, foia_slug, foia_idx):
    """View to redirect agency users to the correct page or offer to resend
    them their login token"""

    agency = get_object_or_404(Agency, slug=agency_slug, pk=agency_idx)
    foia = get_object_or_404(
            FOIARequest,
            agency=agency,
            slug=foia_slug,
            pk=foia_idx,
            )

    if request.method == 'POST':
        email = request.POST.get('email', '')
        # valid if this email is associated with the agency
        valid = (EmailAddress.objects
                .fetch(email)
                .agencies
                .filter(id=agency.pk)
                .exists()
                )
        if valid:
            msg = TemplateEmail(
                    subject='Login Token',
                    from_email='info@muckrock.com',
                    to=[email],
                    text_template='accounts/email/login_token.txt',
                    html_template='accounts/email/login_token.html',
                    extra_context={
                        'reply_link': foia.get_agency_reply_link(email=email),
                        }
                    )
            msg.send(fail_silently=False)
            messages.success(
                    request,
                    'Fresh login token succesfully sent to %s.  '
                    'Please check your email'
                    % email,
                    )
        else:
            messages.error(request, 'Invalid email')
        return redirect(foia)

    authed = request.user.is_authenticated()
    agency_user = authed and request.user.profile.acct_type == 'agency'
    agency_match = agency_user and request.user.profile.agency == agency
    email = request.GET.get('email', '')
    # valid if this email is associated with the agency
    valid = (EmailAddress.objects
            .fetch(email)
            .agencies
            .filter(id=agency.pk)
            .exists()
            )

    if agency_match:
        return redirect(foia)
    elif agency_user:
        return redirect('foia-agency-list')
    elif authed:
        return redirect('index')
    else:
        return render(
                request,
                'accounts/agency_redirect_login.html',
                {'email': email, 'valid': valid},
                )
