from django import forms
from formwizard.contrib.forms import NamedUrlSessionFormWizard
from django.http import HttpResponse
from django.template import Template, Context
from django.contrib.auth.models import User
from django.forms.formsets import formset_factory

class Page1(forms.Form):
    name = forms.CharField(max_length=100)
    user = forms.ModelChoiceField(queryset=User.objects.all())
    thirsty = forms.NullBooleanField()

class Page2(forms.Form):
    address1 = forms.CharField(max_length=100)
    address2 = forms.CharField(max_length=100)
    
class Page3(forms.Form):
    random_crap = forms.CharField(max_length=100)

Page4 = formset_factory(Page3, extra=2)

class ContactWizard(NamedUrlSessionFormWizard):
    def done(self, request, form_list):
        c = Context({'form_list': [x.cleaned_data for x in form_list], 'all_cleaned_data': self.get_all_cleaned_data()})
        for form in self.form_list.keys():
            c[form] = self.get_cleaned_data_for_step(form)

        c['this_will_fail'] = self.get_cleaned_data_for_step('this_will_fail')
        return HttpResponse(Template('').render(c))