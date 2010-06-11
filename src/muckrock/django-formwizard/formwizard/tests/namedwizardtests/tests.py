import re
from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from formwizard.contrib.forms import NamedUrlSessionFormWizard
from formwizard.tests.formtests import get_request, Step1, Step2


class NamedWizardTests(object):
    urls = 'formwizard.tests.namedwizardtests.urls'

    wizard_step_data = (
        {
            'form1-name': 'Pony',
            'form1-thirsty': '2',
        },
        {
            'form2-address1': '123 Main St',
            'form2-address2': 'Djangoland',
        },
        {
            'form3-random_crap': 'blah blah',
        },
        {
            'form4-INITIAL_FORMS': '0',
            'form4-TOTAL_FORMS': '2',
            'form4-MAX_NUM_FORMS': '0',
            'form4-0-random_crap': 'blah blah',
            'form4-1-random_crap': 'blah blah',
        }
    )

    def setUp(self):
        self.client = Client()
        self.testuser, created = User.objects.get_or_create(username='testuser1')
        self.wizard_step_data[0]['form1-user'] = self.testuser.pk

    def test_initial_call(self):
        response = self.client.get(reverse('%s_start' % self.wizard_urlname))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')
        self.assertEqual(response.context['form_step0'], 0)
        self.assertEqual(response.context['form_step1'], 1)
        self.assertEqual(response.context['form_last_step'], 'form4')
        self.assertEqual(response.context['form_prev_step'], None)
        self.assertEqual(response.context['form_next_step'], 'form2')
        self.assertEqual(response.context['form_step_count'], 4)

    def test_form_post_error(self):
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step':'form1'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')
        self.assertEqual(response.context['form'].errors, {'name': [u'This field is required.'], 'user': [u'This field is required.']})

    def test_form_post_success(self):
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step':'form1'}), self.wizard_step_data[0])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form2')
        self.assertEqual(response.context['form_step0'], 1)
        self.assertEqual(response.context['form_prev_step'], 'form1')
        self.assertEqual(response.context['form_next_step'], 'form3')

    def test_form_stepback(self):
        response = self.client.get(reverse(self.wizard_urlname, kwargs={'step':'form1'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step':'form1'}), self.wizard_step_data[0])
        response = self.client.get(response['Location'])
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form2')

        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), {'form_prev_step': response.context['form_prev_step']})
        response = self.client.get(response['Location'])
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

    def test_form_jump(self):
        response = self.client.get(reverse(self.wizard_urlname, kwargs={'step':'form1'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

        response = self.client.get(reverse(self.wizard_urlname, kwargs={'step':'form3'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form3')

    def test_form_finish(self):
        response = self.client.get(reverse(self.wizard_urlname, kwargs={'step': 'form1'}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[0])
        response = self.client.get(response['Location'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form2')

        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[1])
        response = self.client.get(response['Location'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form3')

        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[2])
        response = self.client.get(response['Location'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form4')

        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[3])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['form_list'], [{'name': u'Pony', 'thirsty': True, 'user': self.testuser}, {'address1': u'123 Main St', 'address2': u'Djangoland'}, {'random_crap': u'blah blah'}, [{'random_crap': u'blah blah'}, {'random_crap': u'blah blah'}]])

    def test_cleaned_data(self):
        response = self.client.get(reverse(self.wizard_urlname, kwargs={'step': 'form1'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[0])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[1])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[2])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[3])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['all_cleaned_data'], {'name': u'Pony', 'thirsty': True, 'user': self.testuser, 'address1': u'123 Main St', 'address2': u'Djangoland', 'random_crap': u'blah blah', 'formset-form4': [{'random_crap': u'blah blah'}, {'random_crap': u'blah blah'}]})

    def test_manipulated_data(self):
        response = self.client.get(reverse(self.wizard_urlname, kwargs={'step': 'form1'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[0])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[1])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[2])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        self.client.cookies.pop('sessionid', None)
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step': response.context['form_step']}), self.wizard_step_data[3])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('form_step', None), 'form1')

    def test_form_reset(self):
        response = self.client.post(reverse(self.wizard_urlname, kwargs={'step':'form1'}), self.wizard_step_data[0])
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form2')

        response = self.client.get('%s?reset=1' % reverse('%s_start' % self.wizard_urlname))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

class NamedSessionWizardTests(NamedWizardTests, TestCase):
    wizard_urlname = 'nwiz_session'

class NamedFormTests(TestCase):
    urls = 'formwizard.tests.namedwizardtests.urls'

    def test_add_extra_context(self):
        request = get_request()

        testform = NamedUrlSessionFormWizard([('start', Step1), ('step2', Step2)], url_name='nwiz_session')

        response = testform(request, step='form1', extra_context={'key1': 'value1'})
        self.assertEqual(testform.get_extra_context(), {'key1': 'value1'})

        testform.reset_wizard()

        response = testform(request, extra_context={'key2': 'value2'})
        self.assertEqual(testform.get_extra_context(), {'key2': 'value2'})

    def test_revalidation(self):
        request = get_request()

        testform = NamedUrlSessionFormWizard([('start', Step1), ('step2', Step2)], url_name='nwiz_session')
        response = testform(request, step='done')
        testform.render_done(None)
        self.assertEqual(testform.storage.get_current_step(), 'start')
