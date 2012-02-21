from StringIO import StringIO
from unittest import TestCase

from pyazure.storage import BlobStorage
from django.conf import settings


class SaveTestCase(TestCase):
    def setUp(self):
        self.blob = BlobStorage(settings.AZURE_FILES['account_name'],
                                settings.AZURE_FILES['key'],
                                False)
        self.container = settings.AZURE_FILES['container_name']

    def tearDown(self):
        for blob in self.blob.list_blobs(self.container):
            self.blob.delete_blob(self.container, blob[0])

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
