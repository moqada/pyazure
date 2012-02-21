from StringIO import StringIO
from unittest import TestCase
from urllib2 import urlopen

from pyazure.storage.django_storage import AzureBlockStorage


class SaveTestCase(TestCase):
    def setUp(self):
        self.storage = AzureBlockStorage()

    def tearDown(self):
        for blob in self.storage.connection.blobs.list_blobs(self.storage.container_name):
            self.storage.connection.blobs.delete_blob(self.storage.container_name, blob[0])

    def test_content_type(self):
        content = 'SomeTestText'
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
        content = 'AnotherTestText'
        name = 'unknown'
        content_type = 'application/octet-stream' # Default Content-Type

        name = self.storage.save(name, StringIO(content))
        url = self.storage.url(name)
        response = urlopen(url)
        self.assertEqual(200, response.code)
        self.assertEqual(str(len(content)), response.headers.get('Content-Length'))
        self.assertEqual(content_type, response.headers.get('Content-Type'))
        self.assertEqual(content, response.read())
