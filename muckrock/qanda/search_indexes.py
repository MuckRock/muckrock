"""
Search Index for the Question application
"""

from celery_haystack.indexes import CelerySearchIndex
from haystack.indexes import CharField, Indexable

from muckrock.qanda.models import Question

class QuestionIndex(CelerySearchIndex, Indexable):
    """Search index for questions"""
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')

    def get_model(self):
        """Return model for index"""
        return Question
