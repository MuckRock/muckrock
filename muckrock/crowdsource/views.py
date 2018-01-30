# -*- coding: utf-8 -*-
"""Views for the crowdsource app"""

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import StreamingHttpResponse, Http404
from django.shortcuts import redirect
from django.utils.text import slugify
from django.views.generic import (
        CreateView,
        DetailView,
        FormView,
        UpdateView,
        )
from django.views.generic.detail import BaseDetailView

from itertools import chain
import unicodecsv as csv

from muckrock.accounts.utils import miniregister, mailchimp_subscribe
from muckrock.crowdsource.forms import (
        CrowdsourceAssignmentForm,
        CrowdsourceForm,
        CrowdsourceDataFormset,
        )
from muckrock.crowdsource.models import (
        Crowdsource,
        CrowdsourceResponse,
        )
from muckrock.utils import Echo
from muckrock.views import (
        class_view_decorator,
        MROrderedListView,
        )


class CrowdsourceDetailView(DetailView):
    """A view for the crowdsource owner to view the particular crowdsource"""
    template_name = 'crowdsource/detail.html'
    pk_url_kwarg = 'idx'
    query_pk_and_slug = True
    context_object_name = 'crowdsource'
    queryset = (Crowdsource.objects
            .select_related('user')
            .prefetch_related('data')
            )

    def get(self, request, *args, **kwargs):
        """Redirect to assignment page for non owner, non staff"""
        crowdsource = self.get_object()
        is_owner = self.request.user == crowdsource.user
        if not is_owner and not self.request.user.is_staff:
            return redirect(
                    'crowdsource-assignment',
                    slug=crowdsource.slug,
                    idx=crowdsource.pk,
                    )
        elif self.request.GET.get('csv'):
            return self.results_csv()
        elif self.request.GET.get('dataset'):
            return self.create_dataset()
        else:
            return super(CrowdsourceDetailView, self).get(request, *args, **kwargs)

    def results_csv(self):
        """Return the results in CSV format"""
        crowdsource = self.get_object()
        metadata_keys = crowdsource.get_metadata_keys()
        psuedo_buffer = Echo()
        writer = csv.writer(psuedo_buffer)
        response = StreamingHttpResponse(
                chain(
                    [writer.writerow(crowdsource.get_header_values(metadata_keys))],
                    (writer.writerow(csr.get_values(metadata_keys))
                        for csr in crowdsource.responses.all()),
                    ),
                content_type='text/csv',
                )
        response['Content-Disposition'] = 'attachment; filename="requests.csv"'
        return response

    def create_dataset(self):
        """Create a dataset from a crowdsource's responses"""
        from muckrock.dataset.models import DataSet
        crowdsource = self.get_object()
        dataset = DataSet.objects.create_from_crowdsource(
                self.request.user,
                crowdsource,
                )
        return redirect(dataset)


class CrowdsourceFormView(BaseDetailView, FormView):
    """A view for a user to fill out the crowdsource form"""
    template_name = 'crowdsource/form.html'
    form_class = CrowdsourceAssignmentForm
    pk_url_kwarg = 'idx'
    query_pk_and_slug = True
    context_object_name = 'crowdsource'
    queryset = Crowdsource.objects.filter(status__in=['draft', 'open'])

    def dispatch(self, request, *args, **kwargs):
        """Check permissions"""
        # pylint: disable=attribute-defined-outside-init
        self.object = self.get_object()
        project_only = self.object.project_only and self.object.project
        owner_or_staff = (request.user.is_staff or
                request.user == self.object.user)
        is_contributor = (self.object.project and
                self.object.project.has_contributor(request.user))
        user_allowed = owner_or_staff or is_contributor
        if self.object.status == 'draft' and not owner_or_staff:
            raise Http404
        if project_only and not user_allowed:
            messages.error(request, 'That crowdsource is private')
            return redirect('crowdsource-list')
        return super(CrowdsourceFormView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Cache the object for POST requests"""
        # pylint: disable=attribute-defined-outside-init
        crowdsource = self.get_object()
        data_id = self.request.POST.get('data_id')
        if data_id:
            self.data = crowdsource.data.filter(pk=data_id).first()
        else:
            self.data = None

        if crowdsource.status == 'draft':
            messages.error(request, 'No submitting to draft crowdsources')
            return redirect(crowdsource)
        if request.POST.get('submit') == 'Skip':
            return self.skip()
        return super(CrowdsourceFormView, self).post(request, args, kwargs)

    def get(self, request, *args, **kwargs):
        """Check if there is a valid assignment"""
        has_assignment = self._has_assignment(
                self.get_object(),
                self.request.user,
                )
        if has_assignment:
            return super(CrowdsourceFormView, self).get(request, args, kwargs)
        else:
            messages.warning(
                    request,
                    'Sorry, there are no assignments left for you to complete '
                    'at this time for that crowdsource',
                    )
            return redirect('crowdsource-list')

    def _has_assignment(self, crowdsource, user):
        """Check if the user has a valid assignment to complete"""
        # pylint: disable=attribute-defined-outside-init
        if user.is_anonymous:
            user = None
        self.data = crowdsource.get_data_to_show(user)
        if crowdsource.data.exists():
            return self.data is not None
        else:
            return not (crowdsource.user_limit and
                crowdsource.responses.filter(user=user).exists())

    def get_form_kwargs(self):
        """Add the crowdsource object to the form"""
        kwargs = super(CrowdsourceFormView, self).get_form_kwargs()
        kwargs.update({
            'crowdsource': self.get_object(),
            'user': self.request.user,
            })
        return kwargs

    def get_context_data(self, **kwargs):
        """Get the data source to show, if there is one"""
        if 'data' not in kwargs:
            kwargs['data'] = self.data
        if (self.object.multiple_per_page and
                self.request.user.is_authenticated):
            kwargs['number'] = (self.object.responses
                    .filter(
                        user=self.request.user,
                        data=kwargs['data'],
                        )
                    .count() + 1
                    )
        else:
            kwargs['number'] = 1
        return super(CrowdsourceFormView, self).get_context_data(**kwargs)

    def get_initial(self):
        """Fetch the crowdsource data item to show with this form,
        if there is one"""
        if self.request.method == 'GET' and self.data is not None:
            return {'data_id': self.data.pk}
        else:
            return {}

    def _minireg(self, data):
        """Mini-register a new user if needed"""
        if self.request.user.is_authenticated:
            return self.request.user
        else:
            user, password = miniregister(data['full_name'], data['email'])
            user = authenticate(
                    username=user.username,
                    password=password,
                    )
            login(self.request, user)
            if data.get('newsletter'):
                mailchimp_subscribe(self.request, user.email)
            return user

    def form_valid(self, form):
        """Save the form results"""
        crowdsource = self.get_object()
        has_data = crowdsource.data.exists()
        user = self._minireg(form.cleaned_data)
        number = (self.object.responses
                .filter(user=user, data=self.data)
                .count() + 1
                )
        if not has_data or self.data is not None:
            response = CrowdsourceResponse.objects.create(
                    crowdsource=crowdsource,
                    user=user,
                    data=self.data,
                    number=number,
                    )
            response.create_values(form.cleaned_data)
            messages.success(self.request, 'Thank you!')

        if self.request.POST['submit'] == 'Submit and Add Another':
            return self.render_to_response(
                    self.get_context_data(data=self.data),
                    )

        if has_data:
            return redirect(
                    'crowdsource-assignment',
                    slug=crowdsource.slug,
                    idx=crowdsource.pk,
                    )
        else:
            return redirect('crowdsource-list')

    def form_invalid(self, form):
        """Make sure we include the data in the context"""
        return self.render_to_response(
                self.get_context_data(form=form, data=self.data))

    def skip(self):
        """The user wants to skip this data"""
        crowdsource = self.get_object()
        if (self.data is not None
                and self.request.user.is_authenticated):
            CrowdsourceResponse.objects.create(
                    crowdsource=crowdsource,
                    user=self.request.user,
                    data=self.data,
                    skip=True,
                    )
            messages.info(self.request, 'Skipped!')
        return redirect(
                'crowdsource-assignment',
                slug=crowdsource.slug,
                idx=crowdsource.pk,
                )


class CrowdsourceListView(MROrderedListView):
    """List of crowdfunds"""
    model = Crowdsource
    template_name = 'crowdsource/list.html'
    sort_map = {
            'title': 'title',
            'status': 'status',
            'user': 'user',
            'datetime_created': 'datetime_created',
            }

    def get_queryset(self):
        """Get all open crowdsources and all crowdsources you own"""
        queryset = super(CrowdsourceListView, self).get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(
                    Q(user=self.request.user) |
                    Q(status='open')
                    )
        else:
            return queryset.filter(status='open')


@class_view_decorator(user_passes_test(
    lambda u: u.is_staff or (u.is_authenticated and u.profile.experimental)))
class CrowdsourceCreateView(CreateView):
    """Create a crowdsource"""
    model = Crowdsource
    form_class = CrowdsourceForm
    template_name = 'crowdsource/create.html'

    def get_context_data(self, **kwargs):
        """Add the data formset to the context"""
        data = super(CrowdsourceCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            data['data_formset'] = CrowdsourceDataFormset(self.request.POST)
        else:
            data['data_formset'] = CrowdsourceDataFormset()
        return data

    def form_valid(self, form):
        """Save the crowdsource"""
        if self.request.POST.get('submit') == 'start':
            status = 'open'
            msg = 'Crowdsource started'
        else:
            status = 'draft'
            msg = 'Crowdsource created'
        context = self.get_context_data()
        formset = context['data_formset']
        crowdsource = form.save(commit=False)
        crowdsource.slug = slugify(crowdsource.title)
        crowdsource.user = self.request.user
        crowdsource.status = status
        crowdsource.save()
        crowdsource.create_form(form.cleaned_data['form_json'])
        form.process_data_csv(crowdsource)
        if formset.is_valid():
            formset.instance = crowdsource
            formset.save()
        messages.success(self.request, msg)
        return redirect(crowdsource)


@class_view_decorator(login_required)
class CrowdsourceUpdateView(UpdateView):
    """Update a crowdsource"""
    model = Crowdsource
    form_class = CrowdsourceForm
    template_name = 'crowdsource/create.html'
    pk_url_kwarg = 'idx'
    query_pk_and_slug = True

    def dispatch(self, request, *args, **kwargs):
        """Check permissions"""
        # pylint: disable=attribute-defined-outside-init
        crowdsource = self.get_object()
        editable = crowdsource.status == 'draft'
        user_allowed = request.user == crowdsource.user or request.user.is_staff
        if not editable or not user_allowed:
            messages.error(request, 'You may not edit this crowdsource')
            return redirect(crowdsource)
        return super(CrowdsourceUpdateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Set the form JSON in the initial form data"""
        return {'form_json': self.get_object().get_form_json()}

    def get_context_data(self, **kwargs):
        """Add the data formset to the context"""
        data = super(CrowdsourceUpdateView, self).get_context_data(**kwargs)
        CrowdsourceDataFormset.can_delete = True
        if self.request.POST:
            data['data_formset'] = CrowdsourceDataFormset(
                    self.request.POST,
                    instance=self.get_object(),
                    )
        else:
            data['data_formset'] = CrowdsourceDataFormset(instance=self.get_object())
        return data

    def form_valid(self, form):
        """Save the crowdsource"""
        if self.request.POST.get('submit') == 'start':
            status = 'open'
            msg = 'Crowdsource started'
        else:
            status = 'draft'
            msg = 'Crowdsource updated'
        context = self.get_context_data()
        formset = context['data_formset']
        crowdsource = form.save(commit=False)
        crowdsource.slug = slugify(crowdsource.title)
        crowdsource.status = status
        crowdsource.save()
        crowdsource.create_form(form.cleaned_data['form_json'])
        form.process_data_csv(crowdsource)
        if formset.is_valid():
            formset.save()
        messages.success(self.request, msg)
        return redirect(crowdsource)
