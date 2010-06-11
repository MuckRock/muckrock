from formwizard.tests.storagetests import *
from django.test import TestCase, Client
from formwizard.storage.cookie import CookieStorage
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse

class TestCookieStorage(TestStorage, TestCase):
    def get_storage(self):
        return CookieStorage

    def test_manipulated_cookie(self):
        request = get_request()
        storage = self.get_storage()('wizard1', request)

        storage.request.COOKIES[storage.prefix] = storage.create_cookie_data({'key1': 'value1'})
        self.assertEqual(storage.load_cookie_data(), {'key1': 'value1'})

        storage.request.COOKIES[storage.prefix] = 'i_am_manipulated'
        self.assertRaises(SuspiciousOperation, storage.load_cookie_data)
        
        #raise SuspiciousOperation('FormWizard cookie manipulated')


    def test_delete_cookie(self):
        request = get_request()
        storage = self.get_storage()('wizard1', request)

        storage.cookie_data = {'key1': 'value1'}

        response = HttpResponse()
        storage.update_response(response)

        self.assertEqual(response.cookies[storage.prefix].value, storage.create_cookie_data(storage.cookie_data))

        storage.cookie_data = {}
        storage.update_response(response)
        self.assertEqual(response.cookies[storage.prefix].value, '')
        