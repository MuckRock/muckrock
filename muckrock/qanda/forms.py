"""
Forms for Q&A application
"""

from django import forms

from muckrock.qanda.models import Question, Answer

class QuestionForm(forms.ModelForm):
    """A form for a Question"""
    class Meta:
        # pylint: disable=too-few-public-methods
        model = Question
        fields = ['title', 'question']

class AnswerForm(forms.ModelForm):
    """A form for an Answer"""
    answer = forms.CharField(widget=forms.Textarea(), label='')
    class Meta:
        # pylint: disable=too-few-public-methods
        model = Answer
        fields = ['answer']
