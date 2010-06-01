"""Utility functions for the FOIA Application"""

from django.http import QueryDict
from django.template.loader import render_to_string
from django.template import RequestContext

def process_wizard_data(request, tmpl_name):
    """Take the data from the FOIA wizard and prepare it for the FOIA create form"""

    title, request = (s.strip() for s in render_to_string('%s.txt' % tmpl_name,
                                                          request.POST,
                                                          RequestContext(request)).split('====='))
    params = QueryDict('').copy()
    params.update({'title': title, 'request': request})

    return '?%s' % params.urlencode()
