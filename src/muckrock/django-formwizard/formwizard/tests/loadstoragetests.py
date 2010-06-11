from django.test import TestCase
from formwizard.storage import get_storage, MissingStorageModuleException, \
                               MissingStorageClassException
from formwizard.storage.base import BaseStorage

class TestLoadStorage(TestCase):
    def test_load_storage(self):
        self.assertEqual(
            type(get_storage('formwizard.storage.base.BaseStorage', 'wizard1')),
            BaseStorage)

    def test_missing_module(self):
        self.assertRaises(MissingStorageModuleException, get_storage, 
            'formwizard.storage.idontexist.IDontExistStorage', 'wizard1')

    def test_missing_class(self):
        self.assertRaises(MissingStorageClassException, get_storage, 
            'formwizard.storage.base.IDontExistStorage', 'wizard1')
