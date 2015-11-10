"""
Views for the accounts application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from datetime import date
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions, DjangoModelPermissionsOrAnonReadOnly
import json
import logging
import stripe
import sys

from muckrock.accounts.forms import UserChangeForm, RegisterForm
from muckrock.accounts.models import Profile, Statistics
from muckrock.accounts.serializers import UserSerializer, StatisticsSerializer
from muckrock.foia.models import FOIARequest
import muckrock.message
from muckrock.settings import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

def account_logout(request):
    """Logs a user out of their account and redirects to index page"""
    logout(request)
    messages.success(request, 'You have successfully logged out.')
    return redirect('index')

def register(request):
    """Register for a community account"""
    url_redirect = request.GET.get('next', None)
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            login(request, new_user)
            Profile.objects.create(
                user=new_user,
                acct_type='community',
                monthly_requests=0,
                date_update=date.today()
            )
            send_mail(
                'Welcome to MuckRock',
                render_to_string('text/user/welcome.txt', {
                    'user': new_user,
                    'verification_link': new_user.profile.wrap_url(
                        reverse('acct-verify-email'),
                        key=new_user.profile.generate_confirmation_key())
                    }),
                'info@muckrock.com',
                [new_user.email],
                fail_silently=False
            )
            msg = 'Your account was successfully created. '
            msg += 'Welcome to MuckRock!'
            messages.success(request, msg)
            return redirect(url_redirect) if url_redirect else redirect('acct-my-profile')
    else:
        form = RegisterForm()
    return render_to_response(
        'forms/account/register.html',
        {'form': form},
        context_instance=RequestContext(request)
    )

@login_required
def update(request):
    """Update a users information"""

    if request.method == 'POST':
        user_profile = request.user.profile
        form = UserChangeForm(request.POST, instance=user_profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            customer = request.user.profile.customer()
            customer.email = request.user.email
            customer.save()
            user_profile = form.save()
            messages.success(request, 'Your account has been updated.')
            return redirect('acct-my-profile')
    else:
        user_profile = request.user.profile
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        }
        form = UserChangeForm(initial=initial, instance=user_profile)

    return render_to_response('forms/account/update.html', {'form': form},
                              context_instance=RequestContext(request))

def subscribe(request):
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    # this needs to be refactored
    """Subscribe or unsubscribe from a pro account"""

    call_to_action = 'Go Pro!'
    description = ('Are you a journalist, activist, or just planning on filing '
                   'a lot of requests? A Pro subscription might be right for you.')
    button_text = 'Subscribe'
    can_subscribe = True
    can_unsubscribe = not can_subscribe

    if request.user.is_authenticated():
        user_profile = request.user.profile
        acct_type = user_profile.acct_type
        can_subscribe = acct_type == 'community' or acct_type == 'beta'
        can_unsubscribe = acct_type == 'pro'
        if acct_type == 'admin':
            msg = 'You are on staff, you don\'t need a subscription.'
            messages.warning(request, msg)
            return redirect('acct-my-profile')
        elif acct_type == 'proxy':
            msg = ('You have a proxy account. You receive 20 free '
                   'requests a month and do not need a subscription.')
            messages.warning(request, msg)
            return redirect('acct-my-profile')
        elif can_unsubscribe:
            call_to_action = 'Manage Subscription'
            description = ''
            button_text = 'Unsubscribe'
    else:
        description = ('First you will create an account, then be redirected '
                       'back to this page to subscribe.')
        button_text = 'Create Account'

    if request.method == 'POST':
        stripe_token = request.POST.get('stripe_token')
        customer = user_profile.customer()
        error = False
        user_msg = ''
        logger_msg = ''

        if stripe_token:
            try:
                customer.card = stripe_token
                customer.save()
                user_msg = 'Your payment information has been updated.'
                logger_msg = '%s has updated their payment information.' % request.user.username
                if can_subscribe:
                    user_profile.start_pro_subscription()
                    request.session['ga'] = 'pro_started'
                    user_msg = 'Congratulations, you are now subscribed as a pro user!'
                    logger_msg = '%s has subscribed to a pro account.' % request.user.username
            except (stripe.CardError, stripe.InvalidRequestError, ValueError) as exc:
                error = True
                user_msg = 'Payment error. Your card has not been charged.'
                logger_msg = 'Payment error: %s' % exc
        elif can_unsubscribe:
            try:
                user_profile.cancel_pro_subscription()
                request.session['ga'] = 'pro_cancelled'
                user_msg = 'Your user_profileessional subscription has been cancelled.'
                logger_msg = '%s has cancelled their pro subscription.' % request.user.username
            except (stripe.CardError, stripe.InvalidRequestError) as exc:
                error = True
                user_msg = exc
                logger_msg = exc

        if not error:
            messages.success(request, user_msg)
            logger.info(logger_msg)
        else:
            messages.error(request, user_msg)

        return redirect('acct-my-profile')

    context = {
        'can_subscribe': can_subscribe,
        'can_unsubscribe': can_unsubscribe,
        'call_to_action': call_to_action,
        'description': description,
        'button_text': button_text,
        'stripe_pk': STRIPE_PUB_KEY
    }

    return render_to_response(
        'forms/account/subscription.html',
        context,
        context_instance=RequestContext(request)
    )

@login_required
def buy_requests(request):
    """Buy more requests"""
    url_redirect = request.GET.get('next', 'acct-my-profile')
    if request.POST.get('stripe_token', False):
        user_profile = request.user.profile
        try:
            stripe_token = request.POST['stripe_token']
            stripe_email = request.POST['stripe_email']
            metadata = {
                'email': stripe_email,
                'action': 'request-purchase',
            }
            user_profile.pay(stripe_token, 2000, metadata)
        except (stripe.CardError, ValueError) as exc:
            msg = 'Payment error: %s Your card has not been charged.' % exc
            messages.error(request, msg)
            logger.warn('Payment error: %s', exc, exc_info=sys.exc_info())
            return redirect(url_redirect)
        user_profile.num_requests += 4
        user_profile.save()
        request.session['ga'] = 'request_purchase'
        msg = 'Purchase successful. 4 requests have been added to your account.'
        messages.success(request, msg)
        logger.info('%s has purchased requests', request.user.username)
    return redirect(url_redirect)

@login_required
def verify_email(request):
    """Verifies a user's email address"""
    user = request.user
    prof = user.profile
    key = request.GET.get('key')
    if not prof.email_confirmed:
        if key:
            if key == prof.confirmation_key:
                prof.email_confirmed = True
                prof.save()
                messages.success(request, 'Your email address has been confirmed.')
            else:
                messages.error(request, 'Your confirmation key is invalid.')
        else:
            send_mail(
                'Verify Your MuckRock Email',
                render_to_string('text/user/verify_email.txt', {
                    'user': user,
                    'verification_link': user.profile.wrap_url(
                        reverse('acct-verify-email'),
                        key=prof.generate_confirmation_key())
                }),
                'info@muckrock.com',
                [user.email],
                fail_silently=False
            )
            messages.info(request, 'We just sent you an email containing your verification link.')
    else:
        messages.warning(request, 'Your email is already confirmed, no need to verify again!')
    return redirect(prof)

def profile(request, user_name=None):
    """View a user's profile"""
    user = get_object_or_404(User, username=user_name) if user_name else request.user
    requests = FOIARequest.objects.get_viewable(request.user).filter(user=user)
    recent_requests = requests.order_by('-date_submitted')[:5]
    recent_completed = requests.filter(status='done').order_by('-date_done')[:5]
    context = {
        'user_obj': user,
        'recent_requests': recent_requests,
        'recent_completed': recent_completed,
        'stripe_pk': STRIPE_PUB_KEY,
        'sidebar_admin_url': reverse('admin:auth_user_change', args=(user.pk,)),
    }
    return render_to_response(
        'profile/account.html',
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
        logging.error('Unexpected dictionary structure: %s', exception)
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
        muckrock.message.tasks.send_charge_receipt.delay(event_object_id)
    elif event_type == 'invoice.payment_succeeded':
        muckrock.message.tasks.send_invoice_receipt.delay(event_object_id)
    elif event_type == 'invoice.payment_failed':
        muckrock.message.tasks.failed_payment.delay(event_object_id)
    return HttpResponse()


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
