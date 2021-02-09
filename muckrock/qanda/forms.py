"""
Forms for Q&A application
"""

# Django
from django import forms

# MuckRock
from muckrock.qanda.models import Answer


class AnswerForm(forms.ModelForm):
    """A form for an Answer"""

    class Meta:
        model = Answer
        fields = ["answer"]
        widgets = {
            "answer": forms.Textarea(
                attrs={"placeholder": "Write an answer here", "class": "prose-editor"}
            )
        }
        help_texts = {"answer": "Markdown syntax supported"}
