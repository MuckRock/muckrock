"""
Forms for Q&A application
"""

# Django
from django import forms

# MuckRock
from muckrock.foia.models import FOIARequest
from muckrock.qanda.models import Answer, Question


class QuestionForm(forms.ModelForm):
    """A form for a Question"""
    foia = forms.ModelChoiceField(
        queryset=None, required=False, widget=forms.HiddenInput()
    )

    def __init__(self, user=None, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['foia'].queryset = FOIARequest.objects.get_viewable(user)

    class Meta:
        model = Question
        fields = ['title', 'question', 'foia']
        widgets = {
            'question':
                forms.Textarea(
                    attrs={
                        'placeholder': 'Write your question here',
                        'class': 'prose-editor'
                    }
                )
        }
        help_texts = {'question': 'Markdown syntax supported'}


class AnswerForm(forms.ModelForm):
    """A form for an Answer"""

    class Meta:
        model = Answer
        fields = ['answer']
        widgets = {
            'answer':
                forms.Textarea(
                    attrs={
                        'placeholder': 'Write an answer here',
                        'class': 'prose-editor'
                    }
                )
        }
        help_texts = {'answer': 'Markdown syntax supported'}
