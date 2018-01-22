# -*- coding: utf-8 -*-
"""Views for the crowdsource app"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import StreamingHttpResponse
from django.shortcuts import redirect
from django.utils.text import slugify
from django.views.generic import (
        CreateView,
        DetailView,
        FormView,
        ListView,
        )
from django.views.generic.detail import BaseDetailView

from itertools import chain
import unicodecsv as csv

from muckrock.crowdsource.exceptions import NoAssignmentError
from muckrock.crowdsource.forms import (
        CrowdsourceAssignmentForm,
        CrowdsourceForm,
        CrowdsourceDataFormset,
        )
from muckrock.crowdsource.models import (
        Crowdsource,
        CrowdsourceField,
        CrowdsourceResponse,
        CrowdsourceValue,
        )
from muckrock.utils import Echo
from muckrock.views import class_view_decorator


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
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


#@class_view_decorator(login_required)
@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class CrowdsourceFormView(BaseDetailView, FormView):
    """A view for a user to fill out the crowdsource form"""
    template_name = 'crowdsource/form.html'
    form_class = CrowdsourceAssignmentForm
    pk_url_kwarg = 'idx'
    query_pk_and_slug = True
    context_object_name = 'crowdsource'
    queryset = Crowdsource.objects.filter(status='open')

    def post(self, request, *args, **kwargs):
        """Cache the object for POST requests"""
        # pylint: disable=attribute-defined-outside-init
        self.object = self.get_object()
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
            messages.error(
                    request,
                    'Sorry, there are no assignments left for you to complete '
                    'at this time for that crowdsource',
                    )
            return redirect('crowdsource-list')

    def _has_assignment(self, crowdsource, user):
        """Check if the user has a valid assignment to complete"""
        # pylint: disable=attribute-defined-outside-init
        self.data = crowdsource.get_data_to_show(user)
        if crowdsource.data.exists():
            return self.data is not None
        else:
            return not (crowdsource.user_limit and
                crowdsource.responses.filter(user=self.request.user).exists())

    def get_form_kwargs(self):
        """Add the crowdsource object to the form"""
        kwargs = super(CrowdsourceFormView, self).get_form_kwargs()
        kwargs.update({'crowdsource': self.get_object()})
        return kwargs

    def get_context_data(self, **kwargs):
        """Get the data source to show, if there is one"""
        if 'data' not in kwargs:
            kwargs['data'] = self.data
        if self.object.multiple_per_page:
            kwargs['number'] = (self.object.responses
                    .filter(user=self.request.user, data=kwargs['data'])
                    .count() + 1
                    )
        return super(CrowdsourceFormView, self).get_context_data(**kwargs)

    def get_initial(self):
        """Fetch the crowdsource data item to show with this form,
        if there is one"""
        if self.request.method == 'GET' and self.data is not None:
            return {'data_id': self.data.pk}
        else:
            return {}

    def form_valid(self, form):
        """Save the form results"""
        crowdsource = self.get_object()
        data_id = form.cleaned_data.pop('data_id', None)
        has_data = crowdsource.data.exists()
        data = crowdsource.data.filter(pk=data_id).first()
        number = (self.object.responses
                .filter(user=self.request.user, data=data)
                .count() + 1
                )
        if not has_data or data is not None:
            response = CrowdsourceResponse.objects.create(
                    crowdsource=crowdsource,
                    user=self.request.user,
                    data_id=data_id,
                    number=number,
                    )
            for label, value in form.cleaned_data.iteritems():
                field = CrowdsourceField.objects.get(
                        crowdsource=crowdsource,
                        label=label,
                        )
                CrowdsourceValue.objects.create(
                        response=response,
                        field=field,
                        value=value,
                        )
            messages.success(self.request, 'Thank you!')

        if self.request.POST['submit'] == 'Submit and Add Another':
            return self.render_to_response(
                    self.get_context_data(data=data),
                    )

        if has_data:
            return redirect(
                    'crowdsource-assignment',
                    slug=crowdsource.slug,
                    idx=crowdsource.pk,
                    )
        else:
            return redirect('crowdsource-list')

    def skip(self):
        """The user wants to skip this data"""
        crowdsource = self.get_object()
        data_id = self.request.POST.get('data_id')
        if crowdsource.data.filter(pk=data_id).exists():
            CrowdsourceResponse.objects.create(
                    crowdsource=crowdsource,
                    user=self.request.user,
                    data_id=data_id,
                    skip=True,
                    )
            messages.info(self.request, 'Skipped!')
        return redirect(
                'crowdsource-assignment',
                slug=crowdsource.slug,
                idx=crowdsource.pk,
                )


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class CrowdsourceListView(ListView):
    """List of crowdfunds"""
    queryset = Crowdsource.objects.filter(status='open')
    template_name = 'crowdsource/list.html'


#@class_view_decorator(login_required)
@class_view_decorator(user_passes_test(lambda u: u.is_staff))
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
        context = self.get_context_data()
        formset = context['data_formset']
        crowdsource = form.save(commit=False)
        crowdsource.slug = slugify(crowdsource.title)
        crowdsource.user = self.request.user
        crowdsource.status = 'open'
        crowdsource.save()
        crowdsource.create_form(form.cleaned_data['form_json'])
        form.process_data_csv(crowdsource)
        if formset.is_valid():
            formset.instance = crowdsource
            formset.save()
        messages.success(self.request, 'Crowdsource started')
        return redirect(crowdsource)
