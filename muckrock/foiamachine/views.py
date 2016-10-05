"""
FOIAMachine views
"""

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView, CreateView, DetailView, UpdateView, DeleteView, View
from django.views.generic.detail import SingleObjectMixin
from django.utils.decorators import method_decorator

from django_hosts.resolvers import reverse

from muckrock.accounts.forms import RegisterForm
from muckrock.accounts.views import create_new_user
from muckrock.foiamachine.forms import FoiaMachineRequestForm, FoiaMachineCommunicationForm
from muckrock.foiamachine.models import FoiaMachineRequest, FoiaMachineCommunication

class Homepage(TemplateView):
    """FOIAMachine homepage"""
    template_name = 'foiamachine/homepage.html'

    def dispatch(self, *args, **kwargs):
        """If the user is authenticated, redirect to their profile."""
        if self.request.user.is_authenticated():
            return redirect(reverse('profile', host='foiamachine'))
        return super(Homepage, self).dispatch(*args, **kwargs)


class Signup(FormView):
    """Signs up new users"""
    template_name = 'foiamachine/registration/signup.html'
    form_class = RegisterForm

    def get_success_url(self):
        return reverse('profile', host='foiamachine')

    def form_valid(self, form):
        """Create the user and sign them in."""
        user = create_new_user(self.request, form)
        return super(Signup, self).form_valid(form)


class Profile(TemplateView):
    """Detail for a user."""
    template_name = 'foiamachine/profile.html'

    def dispatch(self, *args, **kwargs):
        """If the user is unauthenticated, redirect them to the login view."""
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('profile', host='foiamachine'))
        return super(Profile, self).dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        """Handle bulk actions on requests"""
        action = self.request.POST.get('action')
        requests = self.request.POST.getlist('request')
        if requests:
            requests = FoiaMachineRequest.objects.filter(user=self.request.user, id__in=requests)
        if action == 'delete':
            for foi in requests:
                foi.delete()
        return super(Profile, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Gets context data for the profile."""
        context = super(Profile, self).get_context_data(**kwargs)
        requests = (FoiaMachineRequest.objects.filter(user=self.request.user)
                                              .order_by('-date_created')
                                              .select_related('jurisdiction', 'agency'))
        context.update({
            'requests': requests,
        })
        return context


class FoiaMachineRequestCreateView(CreateView):
    """Create a new request."""
    form_class = FoiaMachineRequestForm
    template_name = 'foiamachine/foi/create.html'

    def dispatch(self, *args, **kwargs):
        """If the user is unauthenticated, redirect them to the login view."""
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('foi-create', host='foiamachine'))
        return super(FoiaMachineRequestCreateView, self).dispatch(*args, **kwargs)

    def get_receiver(self, agency):
        """Create the agency name from its name and email, if it exists."""
        receiver_string = ''
        if not agency:
            return receiver_string
        receiver_string += unicode(agency)
        agency_email = agency.get_email()
        if agency_email:
            receiver_string += ' <%s>' % agency_email
        return receiver_string

    def form_valid(self, form):
        """Create the request then redirect to it."""
        foi = form.save(commit=False)
        foi.user = self.request.user
        foi.save()
        comm = FoiaMachineCommunication.objects.create(
            request=foi,
            sender=(unicode(foi.user) + ' <' + foi.user.email + '>'),
            receiver=self.get_receiver(foi.agency),
            message=foi.generate_letter()
        )
        return redirect(reverse('foi-detail', host='foiamachine', kwargs={
            'slug': foi.slug,
            'pk': foi.pk,
        }))


class FoiaMachineRequestDetailView(DetailView):
    """Show the detail of a FOIA Machine request."""
    model = FoiaMachineRequest
    template_name = 'foiamachine/foi/detail.html'

    def dispatch(self, *args, **kwargs):
        """Only the request's owner may update it."""
        foi = self.get_object()
        if self.request.user != foi.user:
            sharing_code = self.request.GET.get('sharing')
            if sharing_code != foi.sharing_code:
                raise Http404()
        return super(FoiaMachineRequestDetailView, self).dispatch(*args, **kwargs)


class FoiaMachineRequestUpdateView(UpdateView):
    """Update the information saved to a FOIA Machine request."""
    model = FoiaMachineRequest
    form_class = FoiaMachineRequestForm
    template_name = 'foiamachine/foi/update.html'

    def dispatch(self, *args, **kwargs):
        """Only the request's owner may update it."""
        foi = self.get_object()
        # Redirect logged out users to the login page
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('foi-update', host='foiamachine', kwargs=kwargs))
        # Redirect non-owner users to the detail page
        if self.request.user != foi.user:
            return redirect(reverse('foi-detail', host='foiamachine', kwargs=kwargs))
        return super(FoiaMachineRequestUpdateView, self).dispatch(*args, **kwargs)


class FoiaMachineRequestDeleteView(DeleteView):
    """Confirm the delete action."""
    model = FoiaMachineRequest
    template_name = 'foiamachine/foi/delete.html'

    def dispatch(self, *args, **kwargs):
        """Only the request's owner may delete it."""
        foi = self.get_object()
        # Redirect logged out users to the login page
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('foi-delete', host='foiamachine', kwargs=kwargs))
        # Redirect non-owner users to the detail page
        if self.request.user != foi.user:
            return redirect(reverse('foi-detail', host='foiamachine', kwargs=kwargs))
        return super(FoiaMachineRequestDeleteView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        """The success url is the user profile."""
        return reverse('profile', host='foiamachine')


class FoiaMachineCommunicationCreateView(CreateView):
    """Create a new communication on a request."""
    form_class = FoiaMachineCommunicationForm
    template_name = 'foiamachine/comm/create.html'

    def get_foi(self, **kwargs):
        """Given a set of kwargs, return the FOI object for this view."""
        foi_pk = kwargs.get('foi_pk')
        self.foi = FoiaMachineRequest.objects.get(pk=foi_pk)
        return self.foi

    def dispatch(self, *args, **kwargs):
        """Only the request's owner can add a new communication."""
        foi = self.get_foi(**kwargs)
        # Redirect logged out users to the login page
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('comm-create', host='foiamachine', kwargs=kwargs))
        # Redirect non-owner users to the detail page
        if self.request.user != foi.user:
            return redirect(self.foi.get_absolute_url())
        return super(FoiaMachineCommunicationCreateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        """Adds foi to initial form data."""
        initial = super(FoiaMachineCommunicationCreateView, self).get_initial()
        initial['request'] = self.foi
        return initial

    def get_success_url(self):
        """Upon success, return to the request."""
        return self.foi.get_absolute_url()


class FoiaMachineCommunicationUpdateView(UpdateView):
    """Update a communication on a request."""
    model = FoiaMachineCommunication
    form_class = FoiaMachineCommunicationForm
    template_name = 'foiamachine/comm/update.html'

    def get_foi(self, **kwargs):
        """Given a set of kwargs, return the FOI object for this view."""
        foi_pk = kwargs.get('foi_pk')
        self.foi = FoiaMachineRequest.objects.get(pk=foi_pk)
        return self.foi

    def get_queryset(self):
        """Only include communications on the request in the queryset."""
        _queryset = super(FoiaMachineCommunicationUpdateView, self).get_queryset()
        return _queryset.filter(request=self.foi)

    def dispatch(self, *args, **kwargs):
        """Only the request's owner can update a communication."""
        foi = self.get_foi(**kwargs)
        # Redirect logged out users to the login page
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('comm-update', host='foiamachine', kwargs=kwargs))
        # Redirect non-owner users to the detail page
        if self.request.user != foi.user:
            return redirect(self.foi.get_absolute_url())
        return super(FoiaMachineCommunicationUpdateView, self).dispatch(*args, **kwargs)

    def get_initial(self):
        """Adds foi to initial form data."""
        initial = super(FoiaMachineCommunicationUpdateView, self).get_initial()
        initial['request'] = self.foi
        return initial

    def get_success_url(self):
        """Upon success, return to the request."""
        return self.foi.get_absolute_url()


class FoiaMachineCommunicationDeleteView(DeleteView):
    """Delete a communication on a request."""
    model = FoiaMachineCommunication
    template_name = 'foiamachine/comm/delete.html'

    def get_foi(self, **kwargs):
        """Given a set of kwargs, return the FOI object for this view."""
        foi_pk = kwargs.get('foi_pk')
        self.foi = FoiaMachineRequest.objects.get(pk=foi_pk)
        return self.foi

    def get_queryset(self):
        """Only include communications on the request in the queryset."""
        _queryset = super(FoiaMachineCommunicationDeleteView, self).get_queryset()
        return _queryset.filter(request=self.foi)

    def dispatch(self, *args, **kwargs):
        """Only the request's owner can delete a communication."""
        foi = self.get_foi(**kwargs)
        # Redirect logged out users to the login page
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('comm-delete', host='foiamachine', kwargs=kwargs))
        # Redirect non-owner users to the detail page
        if self.request.user != foi.user:
            return redirect(self.foi.get_absolute_url())
        return super(FoiaMachineCommunicationDeleteView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        """Upon success, return to the request."""
        return self.foi.get_absolute_url()


class FoiaMachineRequestShareView(SingleObjectMixin, View):
    """Allows a request owner to enable or disable request sharing."""
    model = FoiaMachineRequest

    def dispatch(self, *args, **kwargs):
        """Only the request's owner may change the request sharing preference."""
        foi = self.get_object()
        # Redirect logged out users to the login page
        if self.request.user.is_anonymous():
            return redirect(reverse('login', host='foiamachine') +
                '?next=' + reverse('foi-share', host='foiamachine', kwargs=kwargs))
        # Redirect non-owner users to the detail page
        if self.request.user != foi.user:
            return redirect(reverse('foi-detail', host='foiamachine', kwargs=kwargs))
        return super(FoiaMachineRequestShareView, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        """Just redirect to the request detail page."""
        return redirect(reverse('foi-detail', host='foiamachine', kwargs=kwargs))

    def post(self, *args, **kwargs):
        """Generate or delete the sharing code based on the action."""
        foi = self.get_object()
        action = self.request.POST.get('action')
        if action == 'enable':
            foi.generate_sharing_code()
        elif action == 'disable':
            foi.sharing_code = ''
            foi.save()
        return redirect(reverse('foi-detail', host='foiamachine', kwargs=kwargs) + '#share')
