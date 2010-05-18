"""
Views for the FOIA application
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.template.defaultfilters import slugify

from datetime import datetime

from foia.forms import FOIARequestForm
from foia.models import FOIARequest, FOIAImage
from accounts.models import RequestLimitError

def _foia_form_handler(request, foia, action):
    """Handle a form for a FOIA request - user to create and update a FOIA request"""

    if request.method == 'POST':
        status_dict = {'Submit': 'submitted', 'Save': 'started'}


        try:
            foia.date_submitted = datetime.now() if request.POST['submit'] == 'Submit' else None
            foia.status = status_dict[request.POST['submit']],

            form = FOIARequestForm(request.POST, instance=foia)

            if form.is_valid():
                request.user.get_profile().make_request()
                foia_request = form.save(commit=False)
                foia_request.slug = slugify(foia_request.title)
                foia_request.save()

                return HttpResponseRedirect(foia_request.get_absolute_url())

        except KeyError:
            # bad post, not possible from web form
            form = FOIARequestForm(instance=foia)
        except RequestLimitError:
            # no requests left
            return render_to_response('foia/foiarequest_error.html',
                                      context_instance=RequestContext(request))

    else:
        form = FOIARequestForm(instance=foia)

    return render_to_response('foia/foiarequest_form.html',
                              {'form': form, 'action': action},
                              context_instance=RequestContext(request))

@login_required
def create(request):
    """File a new FOIA Request"""

    if request.user.get_profile().can_request():
        foia = FOIARequest(user = request.user)
        return _foia_form_handler(request, foia, 'New')
    else:
        return render_to_response('foia/foiarequest_error.html',
                                  context_instance=RequestContext(request))

@login_required
def update(request, user_name, slug):
    """Update a started FOIA Request"""

    user = get_object_or_404(User, username=user_name)
    foia = get_object_or_404(FOIARequest, user=user, slug=slug)

    if not foia.is_editable():
        return render_to_response('error.html',
                 {'message': 'You may only edit non-submitted requests unless a fix is requested'},
                 context_instance=RequestContext(request))
    if foia.user != request.user:
        return render_to_response('error.html',
                 {'message': 'You may only edit your own requests'},
                 context_instance=RequestContext(request))

    return _foia_form_handler(request, foia, 'Update')

@login_required
def list_by_user(request, user_name):
    """List of all FOIA requests by a given user"""

    user = get_object_or_404(User, username=user_name)
    return list_detail.object_list(request, FOIARequest.objects.filter(user=user), paginate_by=10)

@login_required
def detail(request, jurisdiction, user_name, slug):
    """Details of a single FOIA request"""

    user = get_object_or_404(User, username=user_name)
    foia = get_object_or_404(FOIARequest, jurisdiction=jurisdiction, user=user, slug=slug)
    return render_to_response('foia/foiarequest_detail.html',
                              {'object': foia},
                              context_instance=RequestContext(request))

@login_required
def document_detail(request, jurisdiction, user_name, slug, page):
    """Details of a single FOIA request"""

    user = get_object_or_404(User, username=user_name)
    foia = get_object_or_404(FOIARequest, jurisdiction=jurisdiction, user=user, slug=slug)
    doc = get_object_or_404(FOIAImage, foia=foia, page=page)

    return render_to_response('foia/foiarequest_doc_detail.html',
                              {'doc': doc},
                              context_instance=RequestContext(request))
