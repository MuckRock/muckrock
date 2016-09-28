"""
FOIAMachine views
"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView
from django.utils.decorators import method_decorator

from django_hosts.resolvers import reverse

from muckrock.accounts.forms import RegisterForm


class Homepage(TemplateView):
    """FOIAMachine homepage"""
    template_name = 'foiamachine/homepage.html'


class Signup(FormView):
    """Signs up new users"""
    template_name = 'foiamachine/registration/signup.html'
    form_class = RegisterForm

    def create_user(self, form):
        """Create the user from the valid form, then sign them in to their account."""
        form.save()
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        user = authenticate(username, password)
        login(self.request, user)
        return user

    def form_valid(self, form):
        """Create the user and sign them in."""
        user = self.create_user(form)
        return super(Signup, self).form_valid(form)


class Profile(TemplateView):
    """Detail for a user."""
    template_name = 'foiamachine/profile.html'

    def dispatch(self, *args, **kwargs):
        """If the user is unauthenticated, redirect them to the login view."""
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine'))
        return super(Profile, self).dispatch(*args, **kwargs)
