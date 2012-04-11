import mimetypes
import StringIO
import urlparse

from django.conf import settings
from django.core.files import File
from django.core.files.storage import Storage
from django.core.exceptions import ImproperlyConfigured
from pyazure.storage import BlobSharedAccessSignature

try:
    from pyazure import pyazure
except ImportError:
    raise ImproperlyConfigured, "Could not load pyazure dependency.\n"

class AzureBlockStorage(Storage):
    """
    Class AzureBlockStorage provides storing files in Microsoft Azure Blob Storage. 
    """
    
    CONFIG_KEYS = ['account_name', 'key', 'container_name', 'base_url', 'is_private']

    def __init__(self, option=settings.AZURE_FILES):
        """Constructor. 
        
        Constructs object using dictionary either specified in contucotr or in settings.AZURE_FILES. 
        
        @param option dictionary with 'account_name', 'key', 'container_name', 'base_url'  keys. 
        
        option['account_name']
            Azure account to work with
        option['key']
            Secret authentication key for the azure storage account
        option['container_name']
            Container in which to store the files
        option['base_url']
            Url prefix used with filenames. Should be mapped to the view, that returns an image as result. 
        """
        
        if not option or not (option.has_key('account_name') and option.has_key('key') and option.has_key('container_name') and option.has_key('base_url') ):
            raise ValueError("You didn't specify required options")
            
        for key in self.CONFIG_KEYS:
            setattr(self, key, option.get(key, False))
        
        # create storage connection
        self.connection = pyazure.PyAzure(self.account_name, self.key)
        self.access_signature = BlobSharedAccessSignature(self.account_name, self.key)
        
        # create container if neccessary
        for cont in self.connection.blobs.list_containers():
            if cont[0] == self.container_name:
                return
        self.connection.blobs.create_container(self.container_name, not self.is_private)

    def _open(self, name, mode='rb'):
        """Open a file from database. 
        
        @param name filename or relative path to file based on base_url. path should contain only "/", but not "\". Apache sends pathes with "/".
        If there is no such file in the db, returs None
        """
        if not self.exists(name):
            return None
        try:
            inMemFile = StringIO.StringIO(self.connection.blobs.get_blob(self.container_name, name))
            inMemFile.name = name
            inMemFile.mode = mode
            return File(inMemFile)
        except:
            return None

    def _save(self, name, content):
        """Save 'content' as file named 'name'.
        """
        if hasattr(content, 'chunks'):
            content_str = ''.join(chunk for chunk in content.chunks())
        else:
            content_str = content.read()
        self.connection.blobs.put_blob(self.container_name, str(name), content_str,
                                       mimetypes.guess_type(name)[0])
        return name

    def _get_prefix(self, name):
        prefix = ''
        if '/' in name:
            prefix = name.rsplit('/', 1)[0]
        return prefix

    def exists(self, name):
        for blob in self.connection.blobs.list_blobs(
            self.container_name, prefix=self._get_prefix(name)):
            if blob[0] == name:
                return True
        return False

    def get_available_name(self, name):
        return super(AzureBlockStorage, self).get_available_name(name.replace('\\', '/'))

    def delete(self, name):
        if self.exists(name):
            self.connection.blobs.delete_blob(self.container_name, name)

    def url(self, name):
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        url = urlparse.urljoin(self.base_url, name).replace('\\', '/')
        if self.is_private:
            url += '?' + self.access_signature.create_signed_qs(self.container_name, name)
        return url
    
    def size(self, name):
        for blob in self.connection.blobs.list_blobs(
            self.container_name, prefix=self._get_prefix(name)):
            if blob[0] == name:
                return blob[3]
        return 0
