from formwizard.tests.storagetests import *
from django.test import TestCase, Client
from formwizard.storage.session import SessionStorage

class TestSessionStorage(TestStorage, TestCase):
    def get_storage(self):
        return SessionStorage
