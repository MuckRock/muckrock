from django.http import HttpRequest
from django.conf import settings
from django.utils.importlib import import_module
from django.contrib.auth.models import User
from datetime import datetime

def get_request():
    request = HttpRequest()
    engine = import_module(settings.SESSION_ENGINE)
    request.session = engine.SessionStore(None)
    return request

class TestStorage(object):
    def setUp(self):
        self.testuser, created = User.objects.get_or_create(username='testuser1')

    def test_current_step(self):
        request = get_request()
        storage = self.get_storage()('wizard1', request)
        my_step = 2

        self.assertEqual(storage.get_current_step(), None)

        storage.set_current_step(my_step)
        self.assertEqual(storage.get_current_step(), my_step)

        storage.reset()
        self.assertEqual(storage.get_current_step(), None)

        storage.set_current_step(my_step)
        storage2 = self.get_storage()('wizard2', request)
        self.assertEqual(storage2.get_current_step(), None)

    def test_step_data(self):
        request = get_request()
        storage = self.get_storage()('wizard1', request)
        step1 = 'start'
        step_data1 = {'field1': 'data1', 'field2': 'data2', 'field3': datetime.now(), 'field4': self.testuser}

        self.assertEqual(storage.get_step_data(step1), None)

        storage.set_step_data(step1, step_data1)
        self.assertEqual(storage.get_step_data(step1), step_data1)

        storage.reset()
        self.assertEqual(storage.get_step_data(step1), None)

        storage.set_step_data(step1, step_data1)
        storage2 = self.get_storage()('wizard2', request)
        self.assertEqual(storage2.get_step_data(step1), None)

    def test_extra_context(self):
        request = get_request()
        storage = self.get_storage()('wizard1', request)
        extra_context = {'key1': 'data1', 'key2': 'data2', 'key3': datetime.now(), 'key4': self.testuser}

        self.assertEqual(storage.get_extra_context_data(), {})

        storage.set_extra_context_data(extra_context)
        self.assertEqual(storage.get_extra_context_data(), extra_context)

        storage.reset()
        self.assertEqual(storage.get_extra_context_data(), {})

        storage.set_extra_context_data(extra_context)
        storage2 = self.get_storage()('wizard2', request)
        self.assertEqual(storage2.get_extra_context_data(), {})
