from StringIO import StringIO
from unittest import TestCase
from urllib2 import urlopen

from django.conf import settings
from pyazure.storage.django_storage import AzureBlockStorage


class PublicContainerTestCase(TestCase):
    def setUp(self):
        self.storage = AzureBlockStorage()

    def tearDown(self):
        for blob in self.storage.connection.blobs.list_blobs(self.storage.container_name):
            self.storage.connection.blobs.delete_blob(self.storage.container_name, blob[0])

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


class PrivateContainerTestCase(TestCase):
    def setUp(self):
        self.storage = AzureBlockStorage(settings.PRIVATE_AZURE_FILES)

    def tearDown(self):
        for blob in self.storage.connection.blobs.list_blobs(self.storage.container_name):
            self.storage.connection.blobs.delete_blob(self.storage.container_name, blob[0])

    def test_url(self):
        content = 'PrivateContainerTestCase.test_url'
        name = self.storage.save('test.txt', StringIO(content))
        url = self.storage.url(name)
        response = urlopen(url)
        self.assertEqual(200, response.code)
        self.assertEqual(content, response.read())
