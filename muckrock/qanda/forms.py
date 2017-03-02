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
        widgets = {
            'question': forms.Textarea(attrs={
                'placeholder': 'Write your question here',
                'class': 'prose-editor'
            })
        }
        help_texts = {
            'question': 'Markdown syntax supported'
        }

class AnswerForm(forms.ModelForm):
    """A form for an Answer"""
    class Meta:
        # pylint: disable=too-few-public-methods
        model = Answer
        fields = ['answer']
        widgets = {
            'answer': forms.Textarea(attrs={
                'placeholder': 'Write an answer here',
                'class': 'prose-editor'
            })
        }
        help_texts = {
            'answer': 'Markdown syntax supported'
        }
