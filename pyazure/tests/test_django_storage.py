from StringIO import StringIO
from unittest import TestCase
from urllib2 import urlopen

from django.conf import settings
from pyazure.storage.django_storage import AzureBlockStorage
from pyazure.tests.utils import clear_storage


class PublicContainerTestCase(TestCase):
    def setUp(self):
        self.storage = AzureBlockStorage()

    def tearDown(self):
        clear_storage(self.storage.connection.blobs,
                      self.storage.container_name)

    def test_content_type(self):
        content = 'PublicContainerTestCase.test_content_type'
        name = 'test.txt'
        content_type = 'text/plain'

        name = self.storage.save(name, StringIO(content))
        url = self.storage.url(name)
        response = urlopen(url)
        self.assertEqual(200, response.code)
        self.assertEqual(str(len(content)), response.headers.get('Content-Length'))
        self.assertEqual(content_type, response.headers.get('Content-Type'))
        self.assertEqual(content, response.read())

    def test_unknown_content_type(self):
        content = 'PublicContainerTestCase.test_unknown_content_type'
        name = 'unknown'
        content_type = 'application/octet-stream' # Default Content-Type

        name = self.storage.save(name, StringIO(content))
        url = self.storage.url(name)
        response = urlopen(url)
        self.assertEqual(200, response.code)
        self.assertEqual(str(len(content)), response.headers.get('Content-Length'))
        self.assertEqual(content_type, response.headers.get('Content-Type'))
        self.assertEqual(content, response.read())

    def test_windows_path_separator(self):
        """Regression test for window path separator bug
        """
        content = 'PublicContainerTestCase.test_windows_path'
        name = 'some\\path\\test.txt'

        name = self.storage.save(name, StringIO(content))
        url = self.storage.url(name)
        response = urlopen(url)
        self.assertEqual(200, response.code)
        self.assertEqual(content, response.read())

    def test_get_available_name(self):
        name = 'another\\path\\test.txt'

        content1 = 'PublicContainerTestCase.test_get_available_name'
        name1 = self.storage.save(name, StringIO(content1))

        content2 = content1 + ' with another content'
        name2 = self.storage.save(name, StringIO(content2))

        self.assertNotEqual(name1, name2)

        response = urlopen(self.storage.url(name1))
        self.assertEqual(200, response.code)
        self.assertEqual(content1, response.read())

        response = urlopen(self.storage.url(name2))
        self.assertEqual(200, response.code)
        self.assertEqual(content2, response.read())


class PrivateContainerTestCase(TestCase):
    def setUp(self):
        self.storage = AzureBlockStorage(settings.PRIVATE_AZURE_FILES)

    def tearDown(self):
        clear_storage(self.storage.connection.blobs,
            self.storage.container_name)

    def test_url(self):
        content = 'PrivateContainerTestCase.test_url'
        name = self.storage.save('test.txt', StringIO(content))
        url = self.storage.url(name)
        response = urlopen(url)
        self.assertEqual(200, response.code)
        self.assertEqual(content, response.read())
