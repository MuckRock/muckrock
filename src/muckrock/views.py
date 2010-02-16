"""
Views for muckrock project
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response

from forms import MyUserCreationForm, UserChangeForm

# User handling views
def register(request):
    """Register a new user"""

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return HttpResponseRedirect('/accounts/profile/')
    else:
        form = MyUserCreationForm()
    return render_to_response('registration/register.html', {
        'form': form,
        'user': request.user,
    })

@login_required
def update(request):
    """Update a users information"""

    if request.method == 'POST':
        form = UserChangeForm(request.POST)
        form.user = request.user
        if form.is_valid():
            for data, value in form.cleaned_data.iteritems():
                setattr(request.user, data, value)
            request.user.save()
            return HttpResponseRedirect('/accounts/profile/')
    else:
        form = UserChangeForm(initial=request.user.__dict__)

    return render_to_response('registration/update.html', {
        'form': form,
        'user': request.user
    })
