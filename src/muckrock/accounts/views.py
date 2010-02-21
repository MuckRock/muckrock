"""
Views for the accounts application
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.forms import UserCreationForm

from accounts.forms import UserChangeForm
from accounts.models import Profile

def register(request):
    """Register a new user"""

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return HttpResponseRedirect('/accounts/profile/')
    else:
        form = UserCreationForm()
    return render_to_response('registration/register.html', {
        'form': form,
        'user': request.user,
    })

@login_required
def update(request):
    """Update a users information"""

    def get_profile():
        """Get or create the user's profile"""
        try:
            return request.user.get_profile()
        except Profile.DoesNotExist:
            return Profile(user=request.user)

    if request.method == 'POST':
        profile = get_profile()
        form = UserChangeForm(request.POST, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()

            profile = form.save(commit=False)
            profile.save()
            
            return HttpResponseRedirect('/accounts/profile/')
    else:
        profile = get_profile()
        form = UserChangeForm(initial=request.user.__dict__, instance=profile)

    return render_to_response('registration/update.html', {
        'form': form,
        'user': request.user
    })
