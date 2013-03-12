"""Register pingback for FOIA Requests"""

from muckrock.foia.models import FOIARequest
from muckrock.jurisdiction.models import Jurisdiction

def pingback_foia_handler(**kwargs):
    """Get the FOIA request for the pingback"""

    jmodel = Jurisdiction.objects.get(slug=kwargs['jurisdiction'])
    return FOIARequest.objects.get(jurisdiction=jmodel, slug=kwargs['slug'], pk=kwargs['idx'])

