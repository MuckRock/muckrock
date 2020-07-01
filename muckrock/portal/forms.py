"""
Forms for portals
"""

# Django
from django import forms

# MuckRock
from muckrock.core.utils import generate_key
from muckrock.portal.models import PORTAL_TYPES, Portal


class PortalChoiceField(forms.ModelChoiceField):
    """Choice field to display more information about the portal"""

    def label_from_instance(self, obj):
        return '{} ({}) <{}>'.format(
            obj.name,
            obj.get_type_display(),
            obj.url,
        )


class PortalForm(forms.Form):
    """Add an existing or new portal to a request"""

    portal = PortalChoiceField(
        queryset=Portal.objects.none(),
        required=False,
    )
    url = forms.URLField(
        label='URL',
        required=False,
    )
    name = forms.CharField(
        max_length=255,
        required=False,
    )
    type = forms.ChoiceField(choices=PORTAL_TYPES, required=False)

    def __init__(self, *args, **kwargs):
        self.foia = kwargs.pop('foia')
        super(PortalForm, self).__init__(*args, **kwargs)
        self.fields['portal'].queryset = Portal.objects.filter(
            agencies__jurisdiction=self.foia.agency.jurisdiction
        ).distinct()

    def clean_url(self):
        """Ensure unique URL"""
        url = self.cleaned_data['url']
        if url and Portal.objects.filter(url__iexact=url).exists():
            raise forms.ValidationError('Portal with that URL exists')
        return url

    def clean(self):
        """If no portal selected, must supply data for a new one"""
        data = super(PortalForm, self).clean()
        if not (
            data.get('portal') or
            (data.get('url') and data.get('name') and data.get('type'))
        ):
            raise forms.ValidationError(
                'You must either chose an existing portal or supply a url, '
                'name and type for a new portal'
            )

    def save(self):
        """Save the existing or new portal to the FOIA request"""
        portal = self.cleaned_data.get('portal')
        if not portal:
            portal = Portal.objects.create(
                url=self.cleaned_data['url'],
                name=self.cleaned_data['name'],
                type=self.cleaned_data['type'],
            )
        self.foia.portal = portal
        if not self.foia.portal_password:
            self.foia.portal_password = generate_key()
        self.foia.save()
