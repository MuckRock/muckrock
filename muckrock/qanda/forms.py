"""
Forms for Q&A application
"""

from django import forms

from muckrock.foia.models import FOIARequest
from muckrock.qanda.models import Question, Answer

class QuestionForm(forms.ModelForm):
    """A form for a Question"""
    foia = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.HiddenInput()
    )

    def __init__(self, user=None, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['foia'].queryset = FOIARequest.objects.get_viewable(user)

    class Meta:
        # pylint: disable=too-few-public-methods
        model = Question
        fields = ['title', 'question', 'foia']

class AnswerForm(forms.ModelForm):
    """A form for an Answer"""
    answer = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Write an answer here'}))
    class Meta:
        # pylint: disable=too-few-public-methods
        model = Answer
        fields = ['answer']
