"""
Forms for Q&A application
"""

from django import forms

from muckrock.qanda.models import Question, Answer

class QuestionForm(forms.ModelForm):
    """A form for a Question"""
    class Meta:
        # pylint: disable=R0903
        model = Question
        fields = ['title', 'question']

class AnswerForm(forms.ModelForm):
    """A form for an Answer"""
    answer = forms.CharField(widget=forms.Textarea(), label='')
    class Meta:
        # pylint: disable=R0903
        model = Answer
        fields = ['answer']