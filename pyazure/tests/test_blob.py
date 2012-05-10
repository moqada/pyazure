from StringIO import StringIO
from unittest import TestCase

from django.conf import settings

from pyazure.storage import BlobStorage
from pyazure.tests.utils import clear_storage


class SaveTestCase(TestCase):
    def setUp(self):
        self.blob = BlobStorage(settings.AZURE_FILES['account_name'],
                                settings.AZURE_FILES['key'],
                                False)
        self.container = settings.AZURE_FILES['container_name']

    def tearDown(self):
        clear_storage(self.blob, self.container)

    def test_content_type_header(self):
        """Regression test for Content-type header
        """
        content = 'SomeTestText'
        name = 'test.txt'
        content_type = 'text/plain'

        status = self.blob.put_blob(self.container,
                                    name,
                                    content,
                                    content_type)
        self.assertEqual(201, status)
        response = self.blob.get_blob(self.container, name)
        self.assertEqual(content, response)


class ServicePropertiesTestCase(TestCase):
    def setUp(self):
        self.blob = BlobStorage(
            settings.AZURE_FILES['account_name'],
            settings.AZURE_FILES['key'], False)
        self.properties_org = self.blob.get_blob_service_properties()

    def tearDown(self):
        self.blob.set_blob_service_properties(self.properties_org)

    def test_get_blob_service_properties(self):
        properties = self.blob.get_blob_service_properties()
        self.assertTrue('Version' in properties['Logging'])
        self.assertTrue('Version' in properties['Metrics'])
        self.assertTrue(properties['Logging']['Delete'] in ('true', 'false'))
        self.assertTrue(properties['Logging']['Read'] in ('true', 'false'))
        self.assertTrue(properties['Logging']['Write'] in ('true', 'false'))
        self.assertTrue(properties['Metrics']['Enabled'] in ('true', 'false'))
        self.assertTrue(properties['Metrics']['IncludeAPIs'] in ('true', 'false'))
        self.assertTrue(properties['Metrics']['RetentionPolicy']['Enabled'] in ('true', 'false'))
        self.assertTrue(properties['Logging']['RetentionPolicy']['Enabled'] in ('true', 'false'))
        #self.assertEqual('7', properties['Logging']['RetentionPolicy']['Days'])
        #self.assertEqual('7', properties['Metrics']['RetentionPolicy']['Days'])
        #self.assertEqual('2011-08-18', properties['DefaultServiceVersion'])

    def test_set_blob_service_properties(self):
        from copy import deepcopy
        properties = deepcopy(self.properties_org)
        properties['DefaultServiceVersion'] = '2011-08-18'
        self.assertEqual(202, self.blob.set_blob_service_properties(properties))
        new_properties = self.blob.get_blob_service_properties()
        self.assertEqual('2011-08-18', new_properties['DefaultServiceVersion'])
