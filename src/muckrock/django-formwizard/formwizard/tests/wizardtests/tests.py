import re
from django.test import TestCase, Client
from django.contrib.auth.models import User

class WizardTests(object):
    urls = 'formwizard.tests.wizardtests.urls'

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
        response = self.client.get(self.wizard_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')
        self.assertEqual(response.context['form_step0'], 0)
        self.assertEqual(response.context['form_step1'], 1)
        self.assertEqual(response.context['form_last_step'], 'form4')
        self.assertEqual(response.context['form_prev_step'], None)
        self.assertEqual(response.context['form_next_step'], 'form2')
        self.assertEqual(response.context['form_step_count'], 4)

    def test_form_post_error(self):
        response = self.client.post(self.wizard_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')
        self.assertEqual(response.context['form'].errors, {'name': [u'This field is required.'], 'user': [u'This field is required.']})

    def test_form_post_success(self):
        response = self.client.post(self.wizard_url, self.wizard_step_data[0])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form2')
        self.assertEqual(response.context['form_step0'], 1)
        self.assertEqual(response.context['form_prev_step'], 'form1')
        self.assertEqual(response.context['form_next_step'], 'form3')

    def test_form_stepback(self):
        response = self.client.get(self.wizard_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

        response = self.client.post(self.wizard_url, self.wizard_step_data[0])
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form2')

        response = self.client.post(self.wizard_url, {'form_prev_step': response.context['form_prev_step']})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

    def test_form_finish(self):
        response = self.client.get(self.wizard_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form1')

        response = self.client.post(self.wizard_url, self.wizard_step_data[0])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form2')

        response = self.client.post(self.wizard_url, self.wizard_step_data[1])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form3')

        response = self.client.post(self.wizard_url, self.wizard_step_data[2])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form_step'], 'form4')

        response = self.client.post(self.wizard_url, self.wizard_step_data[3])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['form_list'], [{'name': u'Pony', 'thirsty': True, 'user': self.testuser}, {'address1': u'123 Main St', 'address2': u'Djangoland'}, {'random_crap': u'blah blah'}, [{'random_crap': u'blah blah'}, {'random_crap': u'blah blah'}]])

    def test_cleaned_data(self):
        response = self.client.get(self.wizard_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.wizard_url, self.wizard_step_data[0])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.wizard_url, self.wizard_step_data[1])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.wizard_url, self.wizard_step_data[2])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.wizard_url, self.wizard_step_data[3])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['all_cleaned_data'], {'name': u'Pony', 'thirsty': True, 'user': self.testuser, 'address1': u'123 Main St', 'address2': u'Djangoland', 'random_crap': u'blah blah', 'formset-form4': [{'random_crap': u'blah blah'}, {'random_crap': u'blah blah'}]})

    def test_manipulated_data(self):
        response = self.client.get(self.wizard_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.wizard_url, self.wizard_step_data[0])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.wizard_url, self.wizard_step_data[1])
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self.wizard_url, self.wizard_step_data[2])
        self.assertEqual(response.status_code, 200)
        self.client.cookies.pop('sessionid', None)
        self.client.cookies.pop('formwizard_ContactWizard', None)
        response = self.client.post(self.wizard_url, self.wizard_step_data[3])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get('form_step', None), 'form1')

class SessionWizardTests(WizardTests, TestCase):
    wizard_url = '/wiz_session/'

class CookieWizardTests(WizardTests, TestCase):
    wizard_url = '/wiz_cookie/'
