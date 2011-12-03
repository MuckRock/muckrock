"""
Forms for rodeo application
"""

from django import forms

from rodeo.models import RodeoOption, RodeoVote

class RodeoVoteForm(forms.ModelForm):
    """A form for a Rodeo Vote"""

    option = forms.ModelChoiceField(queryset=RodeoOption.objects.none(),
                                    widget=forms.RadioSelect, empty_label=None)

    def __init__(self, *args, **kwargs):
        rodeo = None
        if 'rodeo' in kwargs:
            rodeo = kwargs.pop('rodeo')
        super(RodeoVoteForm, self).__init__(*args, **kwargs)
        self.fields['option'].queryset = RodeoOption.objects.filter(rodeo=rodeo)

    class Meta:
        # pylint: disable=R0903
        model = RodeoVote
        fields = ['option', 'page']
        widgets = {'page': forms.HiddenInput}
