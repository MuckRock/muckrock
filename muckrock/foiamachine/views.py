"""
FOIAMachine views
"""

from django.contrib.auth import authenticate, login
from django.views.generic import TemplateView, FormView

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
