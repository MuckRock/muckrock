"""
Search Index for the FOIA application
"""

from celery_haystack.indexes import CelerySearchIndex
from haystack.indexes import CharField, Indexable

from muckrock.foia.models import FOIARequest

class FOIARequestIndex(CelerySearchIndex, Indexable):
    """Search index for FOIA requests"""
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')

    def get_model(self):
        """Return model for index"""
        return FOIARequest
