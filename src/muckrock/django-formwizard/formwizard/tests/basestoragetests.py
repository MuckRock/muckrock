from django.test import TestCase
from formwizard.storage.base import BaseStorage

class TestBaseStorage(TestCase):
    def setUp(self):
        self.storage = BaseStorage('wizard1')

    def test_get_current_step(self):
        self.assertRaises(NotImplementedError, self.storage.get_current_step)

    def test_set_current_step(self):
        self.assertRaises(NotImplementedError, self.storage.set_current_step, None)

    def test_get_step_data(self):
        self.assertRaises(NotImplementedError, self.storage.get_step_data, None)

    def test_set_step_data(self):
        self.assertRaises(NotImplementedError, self.storage.set_step_data, None, None)

    def test_get_extra_context_data(self):
        self.assertRaises(NotImplementedError, self.storage.get_extra_context_data)

    def test_set_extra_context_data(self):
        self.assertRaises(NotImplementedError, self.storage.set_extra_context_data, None)

    def test_reset(self):
        self.assertRaises(NotImplementedError, self.storage.reset)

    def test_update_response(self):
        self.assertRaises(NotImplementedError, self.storage.update_response, None)
