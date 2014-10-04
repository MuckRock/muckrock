"""
Search Index for the Question application
"""

from haystack.indexes import SearchIndex, CharField
from haystack import site

from muckrock.qanda.models import Question

class QuestionIndex(SearchIndex):
    """Search index for questions"""
    text = CharField(document=True, use_template=True)
    author = CharField(model_attr='user')

site.register(Question, QuestionIndex)