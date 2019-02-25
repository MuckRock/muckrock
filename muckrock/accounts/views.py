"""
Views for the accounts application
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, ListView, RedirectView, TemplateView

# Standard Library
import json
import logging
import sys
from urllib import urlencode

# Third Party
import stripe
from djangosecure.decorators import frame_deny_exempt
from rest_framework.authtoken.models import Token

# MuckRock
from muckrock.accounts.filters import ProxyFilterSet
from muckrock.accounts.forms import (
    BuyRequestForm,
    EmailSettingsForm,
    OrgPreferencesForm,
    ProfileSettingsForm,
)
from muckrock.accounts.mixins import BuyRequestsMixin
from muckrock.accounts.models import Notification, RecurringDonation
from muckrock.accounts.utils import mixpanel_event
from muckrock.agency.models import Agency
from muckrock.communication.models import EmailAddress
from muckrock.core.views import MRFilterListView
from muckrock.crowdfund.models import RecurringCrowdfundPayment
from muckrock.foia.models import FOIARequest
from muckrock.message.email import TemplateEmail
from muckrock.message.tasks import (
    failed_payment,
    send_charge_receipt,
    send_invoice_receipt,
)
from muckrock.news.models import Article
from muckrock.project.models import Project

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class AccountsView(RedirectView):
    """Accounts view redirects to squarelet"""
    url = '{}/plans/'.format(settings.SQUARELET_URL)


def account_logout_helper(request, url):
    """Logout helper to specify the URL"""
    if 'id_token' in request.session:
        params = {
            'id_token_hint': request.session['id_token'],
            'post_logout_redirect_uri': url,
        }
        redirect_url = '{}/openid/end-session?{}'.format(
            settings.SQUARELET_URL, urlencode(params)
        )
    else:
        redirect_url = 'index'
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect(redirect_url)


def account_logout(request):
    """Logs a user out of their account and redirects to squarelet's logout page"""
    return account_logout_helper(request, settings.MUCKROCK_URL + '/')


@method_decorator(login_required, name='dispatch')
class ProfileSettings(TemplateView):
    """Update a users information"""
    template_name = 'accounts/settings.html'

    def post(self, request, **kwargs):
        """Handle form processing"""
        # pylint: disable=unused-argument
        settings_forms = {
            'profile': ProfileSettingsForm,
            'email': EmailSettingsForm,
            'org': OrgPreferencesForm,
        }
        action = request.POST.get('action')
        receipt_form = None
        if action == 'cancel-donations':
            self._handle_cancel_payments('donations', 'cancel-donations')
            return redirect('acct-settings')
        elif action == 'cancel-crowdfunds':
            self._handle_cancel_payments(
                'recurring_crowdfund_payments',
                'cancel-crowdfunds',
            )
            return redirect('acct-settings')
        elif action:
            form = settings_forms[action]
            form = form(
                request.POST,
                request.FILES,
                instance=request.user.profile,
            )
            if form.is_valid():
                form.save()
                messages.success(request, 'Your settings have been updated.')
                return redirect('acct-settings')

        # form was invalid
        context = self.get_context_data(receipt_form=receipt_form)
        return self.render_to_response(context)

    def _handle_cancel_payments(self, attr, arg):
        """Handle cancelling recurring donations or crowdfunds"""
        payments = (
            getattr(self.request.user, attr)
            .filter(pk__in=self.request.POST.getlist(arg))
        )
        attr_type = {
            'donations': 'Donation',
            'recurring_crowdfund_payments': 'Recurring Crowdfund',
        }
        for payment in payments:
            payment.cancel()
            mixpanel_event(
                self.request,
                'Cancel {}'.format(attr_type[attr]),
                {'Amount': payment.amount},
            )
        msg = attr.replace('_', ' ')
        if payments:
            messages.success(
                self.request,
                'The selected {} have been cancelled.'.format(msg),
            )
        else:
            messages.warning(
                self.request,
                'No {} were selected to be cancelled.'.format(msg),
            )

    def get_context_data(self, **kwargs):
        """Returns context for the template"""
        context = super(ProfileSettings, self).get_context_data(**kwargs)
        user_profile = self.request.user.profile
        email_initial = {'email': self.request.user.email}
        profile_form = ProfileSettingsForm(instance=user_profile)
        email_form = EmailSettingsForm(
            initial=email_initial,
            instance=user_profile,
        )
        org_form = OrgPreferencesForm(instance=user_profile)
        # XXX this contains a lot of stuff moving to squarelet
        donations = RecurringDonation.objects.filter(user=self.request.user)
        crowdfunds = RecurringCrowdfundPayment.objects.filter(
            user=self.request.user
        )
        context.update({
            'squarelet_url': settings.SQUARELET_URL,
            'profile_form': profile_form,
            'email_form': email_form,
            'org_form': org_form,
            'donations': donations,
            'crowdfunds': crowdfunds,
        })
        return context


class ProfileView(BuyRequestsMixin, FormView):
    """View a user's profile"""
    template_name = 'accounts/profile.html'
    form_class = BuyRequestForm

    def dispatch(self, request, *args, **kwargs):
        """Get the user and redirect if neccessary"""
        # pylint: disable=attribute-defined-outside-init
        username = kwargs.get('username')
        if username is None:
            return redirect('acct-profile', username=request.user.username)
        self.user = get_object_or_404(User, username=username, is_active=True)
        return super(ProfileView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Get data for the profile page"""
        context_data = super(ProfileView, self).get_context_data(**kwargs)
        queryset = self.user.organizations.order_by('name')
        if self.request.user.is_staff:
            organizations = [o for o in queryset]
        elif self.request.user.is_authenticated:
            # XXX test
            organizations = [
                o for o in
                queryset.filter(Q(private=False) | Q(users=self.request.user))
            ]
        else:
            organizations = [o for o in queryset.filter(private=False)]
        if self.request.user == self.user:
            context_data['admin_organizations'] = (
                self.user.organizations.filter(memberships__admin=True)
            )
        requests = (
            FOIARequest.objects.filter(composer__user=self.user)
            .get_viewable(self.request.user)
            .select_related('agency__jurisdiction__parent__parent')
        )
        recent_requests = requests.order_by('-composer__datetime_submitted')[:5]
        recent_completed = (
            requests.filter(status='done').order_by('-datetime_done')[:5]
        )
        articles = Article.objects.get_published().filter(authors=self.user)[:5]
        projects = Project.objects.get_for_contributor(self.user).get_visible(
            self.request.user
        )[:3]
        context_data.update({
            'user_obj':
                self.user,
            'profile':
                self.user.profile,
            'organizations':
                organizations,
            'projects':
                projects,
            'requests': {
                'all': requests,
                'recent': recent_requests,
                'completed': recent_completed
            },
            'articles':
                articles,
            'sidebar_admin_url':
                reverse('admin:auth_user_change', args=(self.user.pk,)),
            'api_token':
                Token.objects.get_or_create(user=self.user)[0],
        })
        return context_data

    def get_form_kwargs(self):
        """Give the form the current user"""
        kwargs = super(ProfileView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Buy requests"""
        if self.request.user == self.user:
            self.buy_requests(form)
        return redirect('acct-profile', username=self.user.username)


@csrf_exempt
def stripe_webhook(request):
    """Handle webhooks from stripe"""
    if request.method != "POST":
        return HttpResponseNotAllowed(['POST'])

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET,
            )
        else:
            event = json.loads(request.body)

        event_id = event['id']
        event_type = event['type']
        if event_type.startswith(('charge', 'invoice')):
            event_object_id = event['data']['object'].get('id', '')
        else:
            event_object_id = ''
    except (TypeError, ValueError, SyntaxError) as exception:
        logging.error(
            'Stripe Webhook: Error parsing JSON: %s',
            exception,
            exc_info=sys.exc_info(),
        )
        return HttpResponseBadRequest()
    except KeyError as exception:
        logging.error(
            'Stripe Webhook: Unexpected structure: %s in %s',
            exception,
            event,
            exc_info=sys.exc_info(),
        )
        return HttpResponseBadRequest()
    except stripe.error.SignatureVerificationError as exception:
        logging.error(
            'Stripe Webhook: Signature Verification Error: %s',
            sig_header,
            exc_info=sys.exc_info(),
        )
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
        'data': event
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
class NotificationList(ListView):
    """List of notifications for a user."""
    model = Notification
    template_name = 'accounts/notifications_all.html'
    context_object_name = 'notifications'
    title = 'All Notifications'

    def get_queryset(self):
        """Return all notifications for the user making the request."""
        return (
            super(NotificationList, self).get_queryset().for_user(
                self.request.user
            ).order_by('-datetime').select_related('action').prefetch_related(
                'action__actor',
                'action__target',
                'action__action_object',
            )
        )

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
    sort_map = {
        'name': 'profile__full_name',
        'state': 'profile__state',
    }

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Staff only"""
        return super(ProxyList, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Display all proxies"""
        objects = super(ProxyList, self).get_queryset()
        return (
            objects.filter(organizations__plan__slug='proxy')
            .select_related('profile')
        )


def agency_redirect_login(
    request, agency_slug, agency_idx, foia_slug, foia_idx
):
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
        valid = (
            EmailAddress.objects.fetch(email).agencies.filter(id=agency.pk)
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
                'Please check your email' % email,
            )
        else:
            messages.error(request, 'Invalid email')
        return redirect(foia)

    authed = request.user.is_authenticated()
    agency_user = authed and request.user.profile.is_agency_user
    agency_match = agency_user and request.user.profile.agency == agency
    email = request.GET.get('email', '')
    # valid if this email is associated with the agency
    email_address = EmailAddress.objects.fetch(email)
    valid = (
        email_address is not None
        and email_address.agencies.filter(id=agency.pk).exists()
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
            {'email': email,
             'valid': valid},
        )


@frame_deny_exempt
def rp_iframe(request):
    """RP iframe for OIDC sesison management"""
    return render(
        request,
        'accounts/check_session_iframe.html',
        {'settings': settings},
    )
