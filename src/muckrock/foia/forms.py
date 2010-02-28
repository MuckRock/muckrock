"""
Forms for FOIA application
"""

from django import forms
from foia.models import FOIARequest
from django.template.defaultfilters import slugify

class FOIARequestForm(forms.ModelForm):
    """A form for a FOIA Request"""

    def clean(self):
        """Check user and slug are unique together"""

        forms.ModelForm.clean(self)

        user = self.instance.user
        slug = slugify(self.cleaned_data['title'])

        other_foia = FOIARequest.objects.filter(user=user, slug=slug)

        if len(other_foia) != 0:
            raise forms.ValidationError('You already have a FOIA request with a similar title')

        return self.cleaned_data

    class Meta:
        # pylint: disable-msg=R0903
        model = FOIARequest
        fields = ['title', 'jurisdiction', 'agency', 'request']

