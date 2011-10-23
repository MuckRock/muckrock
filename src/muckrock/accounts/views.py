"""
Views for the accounts application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from datetime import datetime, date
import stripe

from settings import MONTHLY_REQUESTS, STRIPE_SECRET_KEY, STRIPE_PUB_KEY
from accounts.forms import UserChangeForm, RegisterFree, RegisterPro, BuyRequestForm
from accounts.models import Profile
from foia.models import FOIARequest

stripe.api_key = STRIPE_SECRET_KEY

def register(request):
    """Pick what kind of account you want to register for"""
    return render_to_response('registration/register.html',
                              context_instance=RequestContext(request))

def register_free(request):
    """Register for a community account"""

    def create_customer(user, **kwargs):
        """Create a stripe customer for community account"""
        # pylint: disable-msg=W0613
        user.get_profile.save_customer()

    template = 'registration/register_free.html'

    return _register_acct(request, 'community', RegisterFree, template, post_hook=create_customer)

def register_pro(request):
    """Register for a pro account"""

    def create_cc(form, user):
        """Create a new CC on file"""
        user.get_profile().save_customer(form.cleaned_data['token'])
        user.get_profile().save_cc(form)

    template = 'registration/cc.html'
    extra_context = {'heading': 'Pro Account', 'pub_key': STRIPE_PUB_KEY}

    return _register_acct(request, 'pro', RegisterPro, template, extra_context, create_cc)

def _register_acct(request, acct_type, form_class, template, extra_context=None, post_hook=None):
    """Register for an account"""
    # pylint: disable-msg=R0913
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

            if post_hook:
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

    def get_profile():
        """Get or create the user's profile"""
        try:
            return request.user.get_profile()
        except Profile.DoesNotExist: # pragma: no cover
            # shouldn't happen
            return Profile(user=request.user, monthly_requests=MONTHLY_REQUESTS,
                           date_update=datetime.now())

    if request.method == 'POST':
        user_profile = get_profile()
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
        user_profile = get_profile()
        form = UserChangeForm(initial=request.user.__dict__, instance=user_profile)

    return render_to_response('registration/update.html', {'form': form},
                              context_instance=RequestContext(request))

@login_required
def update_cc(request):
    """Update a user's CC"""

@login_required
def buy_requests(request):
    """Buy more requests"""

    if request.method == 'POST':
        form = BuyRequestForm(request.POST, request=request)

        if form.is_valid():
            user_profile = request.user.get_profile()
            customer = user_profile.get_customer()

            try:
                if form.cleaned_data['save_cc']:
                    user_profile.save_cc(form)
                if form.cleaned_data['use_on_file'] or form.cleaned_data['save_cc']:
                    stripe.Charge.create(amount=2000, currency='usd', customer=customer.id,
                                         description='Charge for 5 requests to MuckRock.com')
                else:
                    stripe.Charge.create(amount=2000, currency='usd',
                                         card=form.cleaned_data['token'],
                                         description='Charge for 5 requests to MuckRock.com')

                user_profile.num_requests += 5
                user_profile.save()
                messages.success(request, 'Your purchase was succesful')

                return HttpResponseRedirect(reverse('acct-my-profile'))

            except stripe.CardError as exc:
                messages.error(request, 'Payment error: %s' % exc.message)
                return HttpResponseRedirect(reverse('acct-buy-requests'))

    else:
        form = BuyRequestForm(request=request)

    return render_to_response('registration/cc.html', {'form': form, 'heading': 'Buy Requests'},
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
