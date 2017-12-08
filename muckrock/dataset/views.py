# -*- coding: utf-8 -*-
"""
Views for the dataset application
"""

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.edit import FormView

from djangosecure.decorators import frame_deny_exempt
import os.path
import re
from xlrd import XLRDError

from muckrock.dataset.forms import DataSetUploadForm
from muckrock.dataset.models import DataSet
from muckrock.views import class_view_decorator

def detail(request, slug, idx):
    """Show the data"""
    dataset = get_object_or_404(DataSet, slug=slug, pk=idx)
    context = {
            'dataset': dataset,
            'sidebar_admin_url': reverse(
                'admin:dataset_dataset_change',
                args=(dataset.pk,),
                )
            }
    return render(request, 'dataset/detail.html', context)


@frame_deny_exempt
def embed(request, slug, idx):
    """Embed the data set"""
    dataset = get_object_or_404(DataSet, slug=slug, pk=idx)
    return render(
            request,
            'dataset/embed.html',
            {'dataset': dataset},
            )


def _parse_params(get, name, fields):
    """Parse tabulator parameters back into a list of dicts"""
    # tabulator passes params in the form:
    # type[idx][key] where idx is an integer and key is a string
    # find all parameters of this type and convert them into a list
    # of dictionaries.  On any sort of error, just return an empty list
    pattern = re.compile(r'{}\[([0-9]+)\]\[(\w+)\]'.format(name))
    params = {k: v for k, v in get.iteritems() if k.startswith(name)}
    length = len(params) / len(fields)
    # their should be one of each field for each param
    # if it doesn't divide evenly, something went wrong
    if len(params) % len(fields) != 0:
        return []
    # initialize each dict
    dicts = [{} for _ in xrange(length)]
    for key, value in params.iteritems():
        match = pattern.match(key)
        if not match:
            # a parameter was in the wrong format
            return []
        if match.group(2) not in fields:
            # a parameter included an incorrect field
            return []
        dicts[int(match.group(1))][match.group(2)] = value
    return dicts


def data(request, slug, idx):
    """Get the raw data"""

    def get_int(qdict, key, default):
        """Get an integer from a GET/POST query dict"""
        try:
            return int(qdict.get(key, default))
        except ValueError:
            return default

    dataset = get_object_or_404(DataSet, slug=slug, pk=idx)

    page = get_int(request.GET, 'page', 1)
    size = get_int(request.GET, 'size', 20)
    sorters = _parse_params(request.GET, 'sorters', ('field', 'dir'))
    filters = _parse_params(request.GET, 'filters', ('field', 'type', 'value'))

    offset = (page - 1) * size
    fields = {f.slug: f for f in dataset.fields.all()}

    json_data = dataset.rows.values_list('data', flat=True)
    json_data = json_data.sort(fields, sorters)
    json_data = json_data.tabulator_filter(fields, filters)

    total_rows = json_data.count()
    json_data = list(json_data[offset:offset + size])
    last_page = (total_rows + size - 1) / size
    return JsonResponse({
        'data': json_data,
        'last_page': last_page,
        })


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class Create(FormView):
    """Create a data set from a spreadsheet file"""
    template_name = 'forms/dataset.html'
    form_class = DataSetUploadForm

    def form_valid(self, form):
        """Create the data set"""
        data_file = self.request.FILES['data_file']
        ext = os.path.splitext(data_file.name)[1]
        if ext == '.csv':
            dataset = DataSet.objects.create_from_csv(
                    form.cleaned_data['name'],
                    self.request.user,
                    data_file,
                    )
        elif ext in ('.xls', '.xlsx'):
            try:
                dataset = DataSet.objects.create_from_xls(
                        form.cleaned_data['name'],
                        self.request.user,
                        data_file,
                        )
            except XLRDError:
                messages.error(self.request, 'Corrupt excel file')
                return self.form_invalid(form)
        return redirect(dataset)
