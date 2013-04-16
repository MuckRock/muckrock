"""
Forms for Q&A application
"""

from django import forms

from epiceditor.widgets import EpicEditorWidget

from muckrock.qanda.models import Question, Answer

class QuestionForm(forms.ModelForm):
    """A form for a Question"""

    class Meta:
        # pylint: disable=R0903
        model = Question
        fields = ['title', 'question']
        widgets = {'question': EpicEditorWidget(attrs={'style': 'width:450px; height:200px;'},
                                                themes={'editor': 'epic-light-2.css',
                                                        'preview': 'preview-light.css'})}

class AnswerForm(forms.ModelForm):
    """A form for an Answer"""

    class Meta:
        # pylint: disable=R0903
        model = Answer
        fields = ['answer']
        widgets = {'answer': EpicEditorWidget(attrs={'style': 'width:450px; height:200px;'},
                                              themes={'editor': 'epic-light-2.css',
                                                      'preview': 'preview-light.css'})}
