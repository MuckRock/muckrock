"""
FOIAMachine views
"""

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import (
    View,
    TemplateView,
    FormView,
    CreateView,
    DetailView,
    UpdateView,
    DeleteView)
from django.views.generic.detail import SingleObjectMixin

from django_hosts.resolvers import reverse, reverse_host

from muckrock.accounts.forms import RegisterForm
from muckrock.accounts.views import create_new_user
from muckrock.foiamachine.filters import FoiaMachineRequestFilter
from muckrock.foiamachine.forms import (
    FoiaMachineBulkRequestForm,
    FoiaMachineRequestForm,
    FoiaMachineCommunicationForm
)
from muckrock.foiamachine.models import (
    FoiaMachineRequest,
    FoiaMachineCommunication,
    FoiaMachineFile,
    STATUS
)


class LoginRequiredMixin(object):
    """
    Requires the user to login before continuing.
    We can't use the existing decorator because of django_hosts.
    """
    def dispatch(self, *args, **kwargs):
        """If the user is unauthenticated, redirect them to the login view."""
        if self.request.user.is_anonymous():
            messages.warning(self.request, 'You will need to log in first.')
            return redirect(reverse('login', host='foiamachine') +
                '?next=//' + reverse_host('foiamachine') + self.request.get_full_path())
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class RequestOwnerRequiredMixin(LoginRequiredMixin):
    """
    Requires the user to be the owner of the request.
    Builds off the authentication established in the LoginRequiredMixin.
    """
    foi_pk_kwarg = 'pk'

    def get_foi(self, **kwargs):
        """Returns the object on the view."""
        foi_pk = kwargs.get(self.foi_pk_kwarg)
        return FoiaMachineRequest.objects.get(pk=foi_pk)

    def dispatch(self, *args, **kwargs):
        """Checks if the user is the owner"""
        self.foi = self.get_foi(**kwargs)
        if self.request.user.is_authenticated() and self.request.user != self.foi.user:
            messages.error(self.request, 'You do not have permission to do that.')
            return redirect(self.foi.get_absolute_url())
        return super(RequestOwnerRequiredMixin, self).dispatch(*args, **kwargs)


class CommunicationOwnerRequiredMixin(RequestOwnerRequiredMixin):
    """Gets the FOIA from a different kwarg."""
    foi_pk_kwarg = 'foi_pk'


class Homepage(TemplateView):
    """FOIAMachine homepage"""
    template_name = 'foiamachine/views/homepage.html'

    def dispatch(self, *args, **kwargs):
        """If the user is authenticated, redirect to their profile."""
        if self.request.user.is_authenticated():
            return redirect(reverse('profile', host='foiamachine'))
        return super(Homepage, self).dispatch(*args, **kwargs)


class Signup(FormView):
    """Signs up new users"""
    template_name = 'foiamachine/views/registration/signup.html'
    form_class = RegisterForm

    def get_success_url(self):
        return reverse('profile', host='foiamachine')

    def form_valid(self, form):
        """Create the user and sign them in."""
        user = create_new_user(self.request, form)
        welcome_message = 'Welcome to FOIA Machine, %(first_name)s!' % {
            'first_name': user.first_name,
        }
        messages.success(self.request, welcome_message)
        return super(Signup, self).form_valid(form)


class Profile(LoginRequiredMixin, TemplateView):
    """Detail for a user."""
    template_name = 'foiamachine/views/profile.html'

    def post(self, *args, **kwargs):
        """Handle bulk actions on requests"""
        action = self.request.POST.get('action')
        requests = self.request.POST.getlist('request')
        form = FoiaMachineBulkRequestForm(self.request.POST)
        if requests:
            requests = FoiaMachineRequest.objects.filter(user=self.request.user, id__in=requests)
        if action == 'delete':
            for foi in requests:
                foi.delete()
            messages.success(self.request, 'Requests were deleted.')
        elif action == 'set_status' and form.is_valid():
            status = form.cleaned_data['status']
            for foi in requests:
                foi.status = status
                foi.save()
            success_msg = 'Request status changed to %(status)s.' % {
                'status': dict(STATUS)[status],
            }
            messages.success(self.request, success_msg)
        return super(Profile, self).get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Gets context data for the profile."""
        context = super(Profile, self).get_context_data(**kwargs)
        requests = (FoiaMachineRequest.objects.filter(user=self.request.user)
                                              .order_by('-date_created')
                                              .select_related('jurisdiction', 'agency'))
        form = FoiaMachineBulkRequestForm()
        filter_ = FoiaMachineRequestFilter(self.request.GET, queryset=requests)
        context.update({
            'requests': requests,
            'form': form,
            'filter': filter_,
        })
        return context


class FoiaMachineRequestCreateView(LoginRequiredMixin, CreateView):
    """Create a new request."""
    form_class = FoiaMachineRequestForm
    template_name = 'foiamachine/views/foi/create.html'

    def get_receiver(self, agency):
        """Create the agency name from its name and email, if it exists."""
        # pylint: disable=no-self-use
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
        FoiaMachineCommunication.objects.create(
            request=foi,
            sender=(unicode(foi.user) + ' <' + foi.user.email + '>'),
            receiver=self.get_receiver(foi.agency),
            message=foi.generate_letter()
        )
        messages.success(self.request, 'Your request was created.')
        return redirect(reverse('foi-detail', host='foiamachine', kwargs={
            'slug': foi.slug,
            'pk': foi.pk,
        }))


class FoiaMachineRequestDetailView(DetailView):
    """Show the detail of a FOIA Machine request."""
    model = FoiaMachineRequest
    template_name = 'foiamachine/views/foi/detail.html'

    def dispatch(self, *args, **kwargs):
        """Only the request's owner may update it."""
        foi = self.get_object()
        if self.request.user != foi.user:
            messages.warning(self.request, 'You will need to log in first.')
            sharing_code = self.request.GET.get('sharing')
            if sharing_code != foi.sharing_code:
                raise Http404()
        return super(FoiaMachineRequestDetailView, self).dispatch(*args, **kwargs)


class FoiaMachineRequestUpdateView(RequestOwnerRequiredMixin, UpdateView):
    """Update the information saved to a FOIA Machine request."""
    model = FoiaMachineRequest
    form_class = FoiaMachineRequestForm
    template_name = 'foiamachine/views/foi/update.html'

    def get_success_url(self):
        messages.success(self.request, 'Your edits to this request were saved.')
        return super(FoiaMachineRequestUpdateView, self).get_success_url()


class FoiaMachineRequestDeleteView(RequestOwnerRequiredMixin, DeleteView):
    """Confirm the delete action."""
    model = FoiaMachineRequest
    template_name = 'foiamachine/views/foi/delete.html'

    def get_success_url(self):
        """The success url is the user profile."""
        messages.success(self.request, 'Your request was deleted.')
        return reverse('profile', host='foiamachine')


class FoiaMachineCommunicationCreateView(CommunicationOwnerRequiredMixin, CreateView):
    """Create a new communication on a request."""
    form_class = FoiaMachineCommunicationForm
    template_name = 'foiamachine/views/comm/create.html'

    def get_initial(self):
        """Adds foi to initial form data."""
        initial = super(FoiaMachineCommunicationCreateView, self).get_initial()
        initial['request'] = self.foi
        initial['status'] = self.foi.status
        return initial

    def form_valid(self, form):
        """Make sure to set request status and create files when the form is valid."""
        comm = form.save()
        status = form.cleaned_data['status']
        if status:
            comm.request.status = status
            comm.request.save()
        files = form.cleaned_data['files']
        for _file in files:
            FoiaMachineFile.objects.create(communication=comm, file=_file, name=_file.name)
        return super(FoiaMachineCommunicationCreateView, self).form_valid(form)

    def get_success_url(self):
        """Upon success, return to the request."""
        messages.success(self.request, 'The communication was created.')
        return self.foi.get_absolute_url()


class FoiaMachineCommunicationUpdateView(CommunicationOwnerRequiredMixin, UpdateView):
    """Update a communication on a request."""
    model = FoiaMachineCommunication
    form_class = FoiaMachineCommunicationForm
    template_name = 'foiamachine/views/comm/update.html'

    def get_queryset(self):
        """Only include communications on the request in the queryset."""
        _queryset = super(FoiaMachineCommunicationUpdateView, self).get_queryset()
        return _queryset.filter(request=self.foi)

    def get_initial(self):
        """Adds foi to initial form data."""
        initial = super(FoiaMachineCommunicationUpdateView, self).get_initial()
        initial['files'] = self.object.files.all()
        initial['request'] = self.foi
        initial['status'] = self.foi.status
        return initial

    def form_valid(self, form):
        """Make sure to set request status and create files when the form is valid."""
        comm = form.save()
        status = form.cleaned_data['status']
        if status:
            comm.request.status = status
            comm.request.save()
        files = form.cleaned_data['files']
        for _file in files:
            FoiaMachineFile.objects.create(communication=comm, file=_file, name=_file.name)
        return super(FoiaMachineCommunicationUpdateView, self).form_valid(form)

    def get_success_url(self):
        """Upon success, return to the request."""
        messages.success(self.request, 'Your edits to the communication were saved.')
        return self.foi.get_absolute_url()


class FoiaMachineCommunicationDeleteView(CommunicationOwnerRequiredMixin, DeleteView):
    """Delete a communication on a request."""
    model = FoiaMachineCommunication
    template_name = 'foiamachine/views/comm/delete.html'

    def get_queryset(self):
        """Only include communications on the request in the queryset."""
        _queryset = super(FoiaMachineCommunicationDeleteView, self).get_queryset()
        return _queryset.filter(request=self.foi)

    def get_success_url(self):
        """Upon success, return to the request."""
        messages.success(self.request, 'The communication was deleted.')
        return self.foi.get_absolute_url()


class FoiaMachineRequestShareView(RequestOwnerRequiredMixin, SingleObjectMixin, View):
    """Allows a request owner to enable or disable request sharing."""
    model = FoiaMachineRequest

    def get_foi(self, **kwargs):
        """Returns the object instead of finding the request."""
        return self.get_object()

    def get_redirect_url(self, *args, **kwargs):
        """Redirect the user to the correct view."""
        # pylint: disable=unused-argument
        # pylint: disable=no-self-use
        return reverse('foi-detail', host='foiamachine', kwargs=kwargs) + '#share'

    def get(self, *args, **kwargs):
        """Just redirect to the request detail page."""
        return redirect(self.get_redirect_url(*args, **kwargs))

    def post(self, *args, **kwargs):
        """Generate or delete the sharing code based on the action."""
        action = self.request.POST.get('action')
        if action == 'enable':
            self.foi.generate_sharing_code()
            messages.success(self.request, 'Link sharing is now enabled on this request.')
        elif action == 'disable':
            self.foi.sharing_code = ''
            self.foi.save()
            messages.success(self.request, 'Link sharing is now disabled on this request.')
        return redirect(self.get_redirect_url(*args, **kwargs))
