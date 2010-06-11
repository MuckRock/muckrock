from django.test import TestCase
from django import http
from django import forms
from formwizard.forms import FormWizard, SessionFormWizard, CookieFormWizard
from django.conf import settings
from formwizard.storage.session import SessionStorage
from django.utils.importlib import import_module
from django.contrib.auth.models import User

class DummyRequest(http.HttpRequest):
    def __init__(self, POST=None):
        super(DummyRequest, self).__init__()
        self.method = POST and "POST" or "GET"
        if POST is not None:
            self.POST.update(POST)
        self.session = {}
        self._dont_enforce_csrf_checks = True

def get_request(*args, **kwargs):
    request = DummyRequest(*args, **kwargs)
    engine = import_module(settings.SESSION_ENGINE)
    request.session = engine.SessionStore(None)
    return request

class Step1(forms.Form):
    name = forms.CharField()

class Step2(forms.Form):
    name = forms.CharField()

class Step3(forms.Form):
    data = forms.CharField()

class UserForm(forms.ModelForm):
    class Meta:
        model = User

class TestWizard(FormWizard):
    pass

class FormTests(TestCase):
    def test_form_init(self):
        testform = TestWizard('formwizard.storage.session.SessionStorage', [Step1, Step2])
        self.assertEquals(testform.form_list, {u'0': Step1, u'1': Step2})

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        self.assertEquals(testform.form_list, {u'start': Step1, u'step2': Step2})
        
        testform = TestWizard('formwizard.storage.session.SessionStorage', [Step1, Step2, ('finish', Step3)])
        self.assertEquals(testform.form_list, {u'0': Step1, u'1': Step2, u'finish': Step3})

    def test_first_step(self):
        request = get_request()

        testform = TestWizard('formwizard.storage.session.SessionStorage', [Step1, Step2])
        response = testform(request)
        self.assertEquals(testform.determine_step(), u'0')

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        response = testform(request)

        self.assertEquals(testform.determine_step(), 'start')

    def test_persistence(self):
        request = get_request({'name': 'data1'})

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        response = testform(request)
        self.assertEquals(testform.determine_step(), 'start')
        testform.storage.set_current_step('step2')

        testform2 = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        response = testform2(request)
        self.assertEquals(testform2.determine_step(), 'step2')

    def test_repr(self):
        request = get_request()

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        response = testform(request)

        self.assertEqual(repr(testform), "step: start, form_list: {u'start': <class 'formwizard.tests.formtests.Step1'>, u'step2': <class 'formwizard.tests.formtests.Step2'>}, initial_list: {}")

    def test_add_extra_context(self):
        request = get_request()

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])

        response = testform(request, extra_context={'key1': 'value1'})
        self.assertEqual(testform.get_extra_context(), {'key1': 'value1'})

        request.method = 'POST'
        response = testform(request, extra_context={'key1': 'value1'})
        self.assertEqual(testform.get_extra_context(), {'key1': 'value1'})

    def test_form_prefix(self):
        request = get_request()

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        response = testform(request)

        self.assertEqual(testform.get_form_prefix(), 'start')
        self.assertEqual(testform.get_form_prefix('another'), 'another')


    def test_form_initial(self):
        request = get_request()

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)], initial_list={'start': {'name': 'value1'}})
        response = testform(request)

        self.assertEqual(testform.get_form_initial('start'), {'name': 'value1'})
        self.assertEqual(testform.get_form_initial('step2'), {})

    def test_form_instance(self):
        request = get_request()
        the_instance = User()
        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', UserForm), ('step2', Step2)], instance_list={'start': the_instance})
        response = testform(request)

        self.assertEqual(testform.get_form_instance('start'), the_instance)
        self.assertEqual(testform.get_form_instance('non_exist_instance'), None)

    def test_done(self):
        request = get_request()

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        response = testform(request)

        self.assertRaises(NotImplementedError, testform.done, None, None)

    def test_revalidation(self):
        request = get_request()

        testform = TestWizard('formwizard.storage.session.SessionStorage', [('start', Step1), ('step2', Step2)])
        response = testform(request)
        testform.render_done(None)
        self.assertEqual(testform.storage.get_current_step(), 'start')

class SessionFormTests(TestCase):
    def test_init(self):
        request = get_request()
        testform = SessionFormWizard([('start', Step1)])

        self.assertEqual(type(testform(request)), http.HttpResponse)

class CookieFormTests(TestCase):
    def test_init(self):
        request = get_request()
        testform = CookieFormWizard([('start', Step1)])

        self.assertEqual(type(testform(request)), http.HttpResponse)
