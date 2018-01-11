# -*- coding: utf-8 -*-
"""Views for the crowdsource app"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.text import slugify
from django.views.generic import FormView, ListView, CreateView
from django.views.generic.detail import BaseDetailView

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
from muckrock.views import class_view_decorator


@class_view_decorator(login_required)
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
        return super(CrowdsourceFormView, self).post(request, args, kwargs)

    def get(self, request, *args, **kwargs):
        try:
            return super(CrowdsourceFormView, self).get(request, args, kwargs)
        except NoAssignmentError:
            messages.error(
                    request,
                    'Sorry, there are no assignments left for you to complete '
                    'at this time for that crowdsource',
                    )
            return redirect('crowdsource-list')

    def get_form_kwargs(self):
        """Add the crowdsource object to the form"""
        kwargs = super(CrowdsourceFormView, self).get_form_kwargs()
        kwargs.update({'crowdsource': self.get_object()})
        return kwargs

    def get_context_data(self, **kwargs):
        """Get the data source to show, if there is one"""
        # pylint: disable=attribute-defined-outside-init
        crowdsource = self.get_object()
        self.data = crowdsource.get_data_to_show(self.request.user)
        if crowdsource.data.exists() and self.data is None:
            raise NoAssignmentError
        kwargs['data'] = self.data
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
        response = CrowdsourceResponse.objects.create(
                crowdsource=crowdsource,
                user=self.request.user,
                data_id=data_id,
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
        return redirect(crowdsource)


class CrowdsourceListView(ListView):
    """List of crowdfunds"""
    queryset = Crowdsource.objects.filter(status='open')
    template_name = 'crowdsource/list.html'


@class_view_decorator(login_required)
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
        if formset.is_valid():
            formset.instance = crowdsource
            formset.save()
        messages.success(self.request, 'Crowdsource started')
        return redirect('crowdsource-list')
