"""
Views for the accounts application
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from datetime import datetime

from settings import MONTHLY_REQUESTS
from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import Profile

@login_required
def register(request):
    """Register a new user"""

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            Profile.objects.create(user=new_user, monthly_requests=MONTHLY_REQUESTS,
                                   date_update=datetime.now())
            return HttpResponseRedirect(reverse('acct-my-profile'))
    else:
        form = UserCreationForm()
    return render_to_response('registration/register.html',
                              {'form': form, 'user': request.user},
                              context_instance=RequestContext(request))

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

            user_profile = form.save()

            return HttpResponseRedirect(reverse('acct-my-profile'))
    else:
        user_profile = get_profile()
        form = UserChangeForm(initial=request.user.__dict__, instance=user_profile)

    return render_to_response('registration/update.html', {'form': form},
                              context_instance=RequestContext(request))

def profile(request, user_name=None):
    """View a user's profile"""

    if user_name:
        user_obj = get_object_or_404(User, username=user_name)
    else:
        user_obj = request.user

    return render_to_response('registration/profile.html', {'user_obj': user_obj},
                              context_instance=RequestContext(request))
