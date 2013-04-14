"""
Forms for Q&A application
"""

from django import forms

from muckrock.qanda.models import Question, Answer
from epiceditor.widgets import EpicEditorWidget

class QuestionForm(forms.ModelForm):
    """A form for a Question"""

    class Meta:
        # pylint: disable=R0903
        model = Question
        fields = ['title', 'question']
        widgets = {'question': EpicEditorWidget(attrs={'style': 'width:450px; height:200px;'})}

class AnswerForm(forms.ModelForm):
    """A form for an Answer"""

    class Meta:
        # pylint: disable=R0903
        model = Answer
        fields = ['answer']
        widgets = {'answer': EpicEditorWidget(attrs={'style': 'width:450px; height:200px;'})}
