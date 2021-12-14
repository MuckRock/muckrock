"""
Miscellaneous Views for the FOIA application
"""

# Django
from django.contrib.auth.decorators import permission_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

# Third Party
import bleach

# MuckRock
from muckrock.core.views import MRAutocompleteView
from muckrock.foia.codes import CODES
from muckrock.foia.constants import EMAIL_ATTRIBUTES, EMAIL_STYLES, EMAIL_TAGS
from muckrock.foia.models import STATUS, FOIACommunication, FOIARequest


def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # some jurisdiction slugs changed, just ignore the jurisdiction slug passed in
    foia = get_object_or_404(FOIARequest, pk=idx)
    jurisdiction = foia.jurisdiction.slug
    jidx = foia.jurisdiction.pk

    if action == "view":
        return redirect(f"/foi/{jurisdiction}-{jidx}/{slug}-{idx}/")

    if action == "admin-fix":
        action = "admin_fix"

    return redirect(f"/foi/{jurisdiction}-{jidx}/{slug}-{idx}/{action}/")


def acronyms(request):
    """A page with all the acronyms explained"""
    status_dict = dict(STATUS)
    codes = [
        (acro, name, status_dict.get(status, ""), desc)
        for acro, (name, status, desc) in CODES.items()
    ]
    codes.sort()
    return render(request, "staff/acronyms.html", {"codes": codes})


@permission_required("foia.view_rawemail")
def raw(request, idx):
    """Get the raw email for a communication"""
    # pylint: disable=unused-argument
    comm = get_object_or_404(FOIACommunication, pk=idx)
    raw_email = comm.get_raw_email()
    permission = request.user.is_staff or request.user == comm.foia.user
    if not raw_email or not permission:
        raise Http404
    text, html = raw_email.get_text_html()
    if comm.response:
        email = raw_email.email.from_email.email
    else:
        email = ", ".join(e.email for e in raw_email.email.to_emails.all())

    data = {
        "raw": raw_email.raw_email,
        "text": text,
        "html": bleach.clean(
            html,
            tags=EMAIL_TAGS,
            attributes=EMAIL_ATTRIBUTES,
            styles=EMAIL_STYLES,
            strip=True,
        ),
        "html_src": html,
        "response": comm.response,
        "email": email,
    }
    return render(request, "foia/communication/raw.html", data)


class FOIARequestAutocomplete(MRAutocompleteView):
    """Autocomplete for FOIA requests"""

    queryset = FOIARequest.objects.select_related("agency__jurisdiction")
    search_fields = [
        "title",
        "pk",
        "agency__jurisdiction__name",
        "=agency__jurisdiction__abbrev",
        "=agency__jurisdiction__parent__abbrev",
    ]
    template = "autocomplete/foia.html"
    split_words = "and"

    def get_queryset(self):
        """Only show users requests they are allowed to see"""

        queryset = super().get_queryset()
        queryset = queryset.get_viewable(self.request.user)

        return queryset
