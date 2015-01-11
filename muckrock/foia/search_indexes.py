"""
Search Index for the FOIA application
"""

from haystack.indexes import SearchIndex, CharField
from haystack import site

from muckrock.foia.models import FOIARequest

class FOIARequestIndex(SearchIndex):
    """Search index for FOIA requests"""
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')

site.register(FOIARequest, FOIARequestIndex)
