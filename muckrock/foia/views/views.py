"""
Miscellaneous Views for the FOIA application
"""

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect

from muckrock.foia.codes import CODES
from muckrock.foia.models import (
    FOIARequest,
    FOIACommunication,
    STATUS,
    )


def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument

    # some jurisdiction slugs changed, just ignore the jurisdiction slug passed in
    foia = get_object_or_404(FOIARequest, pk=idx)
    jurisdiction = foia.jurisdiction.slug
    jidx = foia.jurisdiction.pk

    if action == 'view':
        return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/' % locals())

    if action == 'admin-fix':
        action = 'admin_fix'

    return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/%(action)s/' % locals())


def acronyms(request):
    """A page with all the acronyms explained"""
    status_dict = dict(STATUS)
    codes = [(acro, name, status_dict.get(status, ''), desc)
             for acro, (name, status, desc) in CODES.iteritems()]
    codes.sort()
    return render(
            request,
            'staff/acronyms.html',
            {'codes': codes},
            )


@user_passes_test(lambda u: u.is_authenticated() and u.profile.is_advanced())
def raw(request, idx):
    """Get the raw email for a communication"""
    # pylint: disable=unused-argument
    comm = get_object_or_404(FOIACommunication, pk=idx)
    raw_email = comm.get_raw_email()
    if raw_email:
        return HttpResponse(
                raw_email.raw_email,
                content_type='text/plain; charset=utf-8',
                )
    else:
        raise Http404
