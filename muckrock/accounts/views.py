"""
Views for the accounts application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from datetime import datetime, date
import json
import logging
import stripe
import sys

from muckrock.accounts.forms import UserChangeForm, CreditCardForm, RegisterFree, RegisterPro, \
                           PaymentForm, UpgradeSubscForm, CancelSubscForm
from muckrock.accounts.models import Profile
from muckrock.foia.models import FOIARequest
from muckrock.settings import MONTHLY_REQUESTS, STRIPE_SECRET_KEY, STRIPE_PUB_KEY

logger = logging.getLogger(__name__)
stripe.api_key = STRIPE_SECRET_KEY

def register(request):
    """Pick what kind of account you want to register for"""
    return render_to_response('registration/register.html',
                              context_instance=RequestContext(request))

def register_free(request):
    """Register for a community account"""

    def create_customer(user, **kwargs):
        """Create a stripe customer for community account"""
        # pylint: disable=W0613
        user.get_profile().save_customer()

    template = 'registration/register_free.html'

    return _register_acct(request, 'community', RegisterFree, template, create_customer)

def register_pro(request):
    """Register for a pro account"""

    def create_cc(form, user):
        """Create a new CC on file"""
        user.get_profile().save_customer(form.cleaned_data['token'])

    template = 'registration/cc.html'
    extra_context = {'heading': 'Pro Account', 'pub_key': STRIPE_PUB_KEY}

    return _register_acct(request, 'pro', RegisterPro, template, create_cc, extra_context)

def _register_acct(request, acct_type, form_class, template, post_hook, extra_context=None):
    """Register for an account"""
    # pylint: disable=R0913
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            Profile.objects.create(user=new_user,
                                   acct_type=acct_type,
                                   monthly_requests=MONTHLY_REQUESTS.get(acct_type, 0),
                                   date_update=datetime.now())

            post_hook(form=form, user=new_user)

            return HttpResponseRedirect(reverse('acct-my-profile'))
    else:
        form = form_class(initial={'expiration': date.today()})

    context = {'form': form}
    if extra_context:
        context.update(extra_context)
    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
def update(request):
    """Update a users information"""

    if request.method == 'POST':
        user_profile = request.user.get_profile()
        form = UserChangeForm(request.POST, instance=user_profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()

            customer = request.user.get_profile().get_customer()
            customer.email = request.user.email
            customer.save()

            user_profile = form.save()

            return HttpResponseRedirect(reverse('acct-my-profile'))
    else:
        user_profile = request.user.get_profile()
        form = UserChangeForm(initial=request.user.__dict__, instance=user_profile)

    return render_to_response('registration/update.html', {'form': form},
                              context_instance=RequestContext(request))

@login_required
def update_cc(request):
    """Update a user's CC"""

    if request.method == 'POST':
        form = CreditCardForm(request.POST)

        if form.is_valid():
            request.user.get_profile().save_cc(form.cleaned_data['token'])
            messages.success(request, 'Your credit card has been saved.')
            return HttpResponseRedirect(reverse('acct-my-profile'))

    else:
        form = CreditCardForm(initial={'name': request.user.get_full_name()})

    card = request.user.get_profile().get_cc()
    if card:
        desc = 'Current card on file: %s ending in %s' % (card.type, card.last4)
    else:
        desc = 'No card currently on file'

    return render_to_response('registration/cc.html',
                              {'form': form, 'pub_key': STRIPE_PUB_KEY, 'desc': desc,
                               'heading': 'Update Credit Card'},
                              context_instance=RequestContext(request))

@login_required
def manage_subsc(request):
    """Subscribe or unsubscribe from a pro account"""

    user_profile = request.user.get_profile()

    if user_profile.acct_type == 'admin':
        heading = 'Admin Account'
        desc = "You are an admin, you don't need a subscription"
        return render_to_response('registration/subsc.html', {'desc': desc, 'heading': heading},
                                  context_instance=RequestContext(request))
    elif user_profile.acct_type == 'beta':
        heading = 'Beta Account'
        desc = 'Thank you for being a beta tester.  You will continue to get 5 ' \
               'free requests a month for helping out.'
        return render_to_response('registration/subsc.html', {'desc': desc, 'heading': heading},
                                  context_instance=RequestContext(request))

    elif user_profile.acct_type == 'community':
        heading = 'Upgrade to a Pro Account'
        desc = 'Upgrade to a professional account. $40 per month for 10 requests per month.'
        form_class = UpgradeSubscForm
        template = 'registration/cc.html'
    elif user_profile.acct_type == 'pro':
        heading = 'Cancel Your Subscription'
        desc = 'You will go back to a free community account.'
        form_class = CancelSubscForm
        template = 'registration/subsc.html'

    if request.method == 'POST':
        form = form_class(request.POST, request=request)

        if user_profile.acct_type == 'community' and form.is_valid():
            if not form.cleaned_data.get('use_on_file'):
                user_profile.save_cc(form.cleaned_data['token'])
            customer = user_profile.get_customer()
            customer.update_subscription(plan='pro')
            user_profile.acct_type = 'pro'
            user_profile.date_update = datetime.now()
            user_profile.monthly_requests = MONTHLY_REQUESTS.get('pro', 0)
            user_profile.save()
            messages.success(request, 'You have been succesfully upgraded to a Pro Account!')
            return HttpResponseRedirect(reverse('acct-my-profile'))
        elif user_profile.acct_type == 'pro' and form.is_valid():
            customer = user_profile.get_customer()
            customer.cancel_subscription()
            user_profile.acct_type = 'community'
            user_profile.save()
            messages.info(request, 'Your professional account subscription has been cancelled')
            return HttpResponseRedirect(reverse('acct-my-profile'))

    else:
        form = form_class(request=request, initial={'name': request.user.get_full_name()})

    return render_to_response(template,
                              {'form': form, 'heading': heading, 'desc': desc,
                               'pub_key': STRIPE_PUB_KEY},
                              context_instance=RequestContext(request))

@login_required
def buy_requests(request):
    """Buy more requests"""

    if request.method == 'POST':
        form = PaymentForm(request.POST, request=request)

        if form.is_valid():
            try:
                user_profile = request.user.get_profile()
                user_profile.pay(form, 2000, 'Charge for 5 requests')
                user_profile.num_requests += 5
                user_profile.save()
                logger.info('%s has purchased requests',  request.user.username)
                return HttpResponseRedirect(reverse('acct-my-profile'))
            except stripe.CardError as exc:
                messages.error(request, 'Payment error: %s' % exc)
                logger.error('Payment error: %s', exc, exc_info=sys.exc_info())
                return HttpResponseRedirect(reverse('acct-buy-requests'))

    else:
        form = PaymentForm(request=request, initial={'name': request.user.get_full_name()})

    return render_to_response('registration/cc.html',
                              {'form': form, 'pub_key': STRIPE_PUB_KEY, 'heading': 'Buy Requests',
                               'desc': 'Buy 5 requests for $20.  They may be used at any time.'},
                              context_instance=RequestContext(request))

def profile(request, user_name=None):
    """View a user's profile"""

    if user_name:
        user_obj = get_object_or_404(User, username=user_name)
    else:
        user_obj = request.user

    foia_requests = FOIARequest.objects.get_viewable(request.user)\
                                       .filter(user=user_obj)\
                                       .order_by('-date_submitted')[:5]

    return render_to_response('registration/profile.html',
                              {'user_obj': user_obj, 'foia_requests': foia_requests},
                              context_instance=RequestContext(request))

@csrf_exempt
def stripe_webhook(request):
    """Handle webhooks from stripe"""
    if 'json' not in request.POST:
        raise Http404

    message = json.loads(request.POST.get('json'))
    event = message.get('event')
    del message['event']

    events = ['recurring_payment_failed', 'invoice_ready', 'recurring_payment_succeeded',
              'subscription_trial_ending', 'subscription_final_payment_attempt_failed', 'ping']

    if event not in events:
        raise Http404

    for key, value in message.iteritems():
        if isinstance(value, dict) and 'object' in value:
            message[key] = stripe.convert_to_stripe_object(value, STRIPE_SECRET_KEY)

    if event == 'recurring_payment_failed':
        user_profile = Profile.objects.get(stripe_id=message['customer'])
        user = user_profile.user
        attempt = message['attempt']
        logger.info('Failed payment by %s, attempt %s', user.username, attempt)
        send_mail('Payment Failed',
                  render_to_string('registration/pay_fail.txt',
                                   {'user': user, 'attempt': attempt}),
                  'info@muckrock.com', [user.email], fail_silently=False)
    elif event == 'subscription_final_payment_attempt_failed':
        user_profile = Profile.objects.get(stripe_id=message['customer'])
        user = user_profile.user
        user_profile.acct_type = 'community'
        user_profile.save()
        logger.info('%s subscription has been cancelled due to failed payment', user.username)
        send_mail('Payment Failed',
                  render_to_string('registration/pay_fail.txt',
                                   {'user': user, 'attempt': 'final'}),
                  'info@muckrock.com', [user.email], fail_silently=False)

    return HttpResponse()

@csrf_exempt
def stripe_webhook_v2(request):
    """Handle webhooks from stripe"""
    # pylint: disable=R0914

    if request.method != "POST":
        return HttpResponse("Invalid Request.", status=400)

    event_json = json.loads(request.raw_post_data)
    event_data = event_json['data']['object']

    logger.info('Received stripe webhook of type %s\nIP: %s\nID:%s\nData: %s' % \
        (event_json['type'], request.META['REMOTE_ADDR'], event_json['id'], event_json))

    description = event_data.get('description')
    customer = event_data.get('customer')
    if description and ':' in description:
        username = description[:description.index(':')]
        user = User.objects.get(username=username)
    elif customer:
        try:
            user = Profile.objects.get(stripe_id=customer).user
        except Profile.DoesNotExist:
            # db is not synced yet, return 404 and let stripe retry - we should be synced by then
            raise Http404
    elif event_json['type'] in ['charge.succeeded', 'invoice.payment_failed']:
        logger.warning('Cannot figure out customer from stripe webhook, no receipt sent: %s'
                       % event_json)
        return HttpResponse()

    if event_json['type'] == 'charge.succeeded':
        amount = event_data['amount'] / 100.0
        base_amount = amount / 1.05
        fee_amount = amount - base_amount

        if event_data.get('description') and \
                event_data['description'].endswith('Charge for 5 requests'):
            type_ = 'community'
            url = '/foia/new/'
            subject = 'Payment received for additional requests'
        elif event_data.get('description') and \
                'Charge for request' in event_data['description']:
            type_ = 'doc'
            url = FOIARequest.objects.get(id=event_data['description'].split()[-1])\
                                     .get_absolute_url()
            subject = 'Payment received for request fee'
        else:
            type_ = 'pro'
            url = '/foia/new/'
            subject = 'Payment received for professional account'

        msg = EmailMessage(subject=subject,
                           body=render_to_string('registration/receipt.txt',
                               {'user': user,
                                'id': event_data['id'],
                                'date': datetime.fromtimestamp(event_data['created']),
                                'amount': amount,
                                'base_amount': base_amount,
                                'fee_amount': fee_amount,
                                'url': url,
                                'type': type_}),
                           from_email='info@muckrock.com',
                           to=[user.email], bcc=['requests@muckrock.com'])
        msg.send(fail_silently=False)

    elif event_json['type'] == 'invoice.payment_failed':
        attempt = event_data['attempt_count']
        user_profile = user.get_profile()
        if attempt == 4:
            user_profile.acct_type = 'community'
            user_profile.save()
            logger.info('%s subscription has been cancelled due to failed payment', user.username)
            msg = EmailMessage(subject='Payment Failed',
                               body=render_to_string('registration/pay_fail.txt',
                                   {'user': user, 'attempt': 'final'}),
                               from_email='info@muckrock.com',
                               to=[user.email], bcc=['requests@muckrock.com'])
            msg.send(fail_silently=False)
        else:
            logger.info('Failed payment by %s, attempt %s', user.username, attempt)
            msg = EmailMessage(subject='Payment Failed',
                               body=render_to_string('registration/pay_fail.txt',
                                   {'user': user, 'attempt': attempt}),
                               from_email='info@muckrock.com',
                               to=[user.email], bcc=['requests@muckrock.com'])
            msg.send(fail_silently=False)

    return HttpResponse()
