"""
Forms for Q&A application
"""

from django import forms

from qanda.models import Question, Answer

class QuestionForm(forms.ModelForm):
    """A form for a Question"""

    class Meta:
        # pylint: disable=R0903
        model = Question
        fields = ['title', 'question']
        widgets = {'question': forms.Textarea(attrs={'style': 'width:450px; height:200px;'})}

class AnswerForm(forms.ModelForm):
    """A form for an Answer"""

    class Meta:
        # pylint: disable=R0903
        model = Answer
        fields = ['answer']
        widgets = {'area': forms.Textarea(attrs={'style': 'width:450px; height:200px;'})}
