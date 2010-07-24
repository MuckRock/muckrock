"""
Views for the FOIA application
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.views.generic import list_detail

from datetime import datetime, timedelta

from foia.forms import FOIARequestForm, FOIADeleteForm, FOIAWizardWhereForm, FOIAWhatLocalForm, \
                       FOIAWhatStateForm, FOIAWhatFederalForm, FOIAWizard, TEMPLATES
from foia.models import FOIARequest, FOIAImage, Jurisdiction
from accounts.models import RequestLimitError
from muckrock.utils import process_get

def _foia_form_handler(request, foia, action):
    """Handle a form for a FOIA request - user to create and update a FOIA request"""

    if request.method == 'POST':
        status_dict = {'Submit': 'submitted', 'Save': 'started'}

        try:
            if request.POST['submit'] == 'Submit':
                foia.date_submitted = datetime.now()
                foia.date_due = datetime.now() + timedelta(15)

            foia.status = status_dict[request.POST['submit']]

            form = FOIARequestForm(request.POST, instance=foia)

            if form.is_valid():
                if request.POST['submit'] == 'Submit':
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
        form = FOIARequestForm(initial=process_get(request.GET), instance=foia)

    return render_to_response('foia/foiarequest_form.html',
                              {'form': form, 'action': action},
                              context_instance=RequestContext(request))

@login_required
def create(request):
    """Create a new foia request using the wizard"""

    # collect all the forms so that the wizard can access them
    form_dict = dict((t.__name__, t) for t in TEMPLATES.values())
    form_dict.update((form.__name__, form) for form in
                     [FOIAWizardWhereForm, FOIAWhatLocalForm,
                      FOIAWhatStateForm, FOIAWhatFederalForm])
    return FOIAWizard(['FOIAWizardWhereForm'], form_dict)(request)

@login_required
def update(request, jurisdiction, slug, idx):
    """Update a started FOIA Request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

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
def delete(request, jurisdiction, slug, idx):
    """Delete a non-submitted FOIA Request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_deletable():
        return render_to_response('error.html',
                 {'message': 'You may only delete non-submitted requests.'},
                 context_instance=RequestContext(request))
    if foia.user != request.user:
        return render_to_response('error.html',
                 {'message': 'You may only delete your own requests'},
                 context_instance=RequestContext(request))

    if request.method == 'POST':
        form = FOIADeleteForm(request.POST)
        if form.is_valid():
            foia.delete()
            messages.info(request, 'Request succesfully deleted')
            return HttpResponseRedirect(reverse('foia-list-user',
                                                kwargs={'user_name': request.user.username}))
    else:
        form = FOIADeleteForm()

    return render_to_response('foia/foiarequest_delete.html',
                              {'form': form, 'foia': foia},
                              context_instance=RequestContext(request))

@login_required
def update_list(request):
    """List of all FOIA requests by a given user"""

    return list_detail.object_list(request,
                                   FOIARequest.objects.get_editable().filter(user=request.user),
                                   paginate_by=10,
                                   template_name='foia/foiarequest_update_list.html')

def list_(request):
    """List all viewable FOIA requests"""

    return list_detail.object_list(request,
                                   FOIARequest.objects.get_viewable(request.user),
                                   paginate_by=10)

def list_by_user(request, user_name):
    """List of all FOIA requests by a given user"""

    user = get_object_or_404(User, username=user_name)
    return list_detail.object_list(request,
                                   FOIARequest.objects.get_viewable(request.user).filter(user=user),
                                   paginate_by=10)

def sorted_list(request, sort_order, field):
    """Sorted list of FOIA requests"""

    if sort_order not in ['asc', 'desc']:
        raise Http404()
    if field not in ['title', 'status', 'user', 'jurisdiction']:
        raise Http404()

    if field == 'jurisdiction':
        field += '__name'
    ob_field = '-' + field if sort_order == 'desc' else field

    return list_detail.object_list(
                request,
                FOIARequest.objects.get_viewable(request.user).order_by(ob_field),
                paginate_by=10,
                extra_context={'sort_by': field, 'sort_order': sort_order})

def detail(request, jurisdiction, slug, idx):
    """Details of a single FOIA request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)

    if not foia.is_viewable(request.user):
        raise Http404()

    context = {'object': foia}
    if foia.date_due:
        context['past_due'] = foia.date_due < datetime.now().date()
    else:
        context['past_due'] = False

    return render_to_response('foia/foiarequest_detail.html',
                              context,
                              context_instance=RequestContext(request))

def document_detail(request, jurisdiction, slug, idx, page):
    """Details of a single FOIA request"""

    jmodel = Jurisdiction.objects.get(slug=jurisdiction)
    foia = get_object_or_404(FOIARequest, jurisdiction=jmodel, slug=slug, id=idx)
    doc = get_object_or_404(FOIAImage, foia=foia, page=page)

    if not foia.is_viewable(request.user):
        raise Http404()

    max_width = 640
    if doc.image.width > max_width:
        width = max_width
        height = int((float(max_width) /  doc.image.width) * doc.image.height)
    else:
        width = doc.image.width
        height = doc.image.height

    return render_to_response('foia/foiarequest_doc_detail.html',
                              {'doc': doc, 'width': width, 'height': height},
                              context_instance=RequestContext(request))
