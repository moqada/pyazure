import base64
import datetime
import hashlib
import hmac
import re
import urllib
from urlparse import urlsplit, urljoin, parse_qs

from pyazure.util import get_azure_time, NEW_LINE

# Helper and Base Classes
################################################################################
class StorageSharedKeyCredentials(object):
    def __init__(self, account_name, account_key, use_path_style_uris = None):
        self._account = account_name
        self._key = base64.decodestring(account_key)

    def _sign_request_impl(self, request, for_tables = False, use_path_style_uris = None):
        (scheme, host, path, query, fragment) = urlsplit(request.get_full_url())
        if use_path_style_uris:
            path = path[path.index('/'):]
        
        if use_path_style_uris is None:
            use_path_style_uris = re.match('^[\d.:]+$', host) is not None

        #RFC 1123
        request.add_header('x-ms-date', get_azure_time())
        canonicalized_headers = NEW_LINE.join(('%s:%s' % (k.lower(), request.get_header(k).strip()) for k in sorted(request.headers.keys(), lambda x,y: cmp(x.lower(), y.lower())) if k.lower().startswith("x-ms-")))

        # verb
        string_to_sign = request.get_method().upper() + NEW_LINE
        
        for field in ['Content-encoding', 'Content-language', 'Content-length', 'Content-MD5', 'Content-type']:
            if request.has_header(field):
                string_to_sign += request.get_header(field)
            string_to_sign += NEW_LINE
        
        # Date
        if for_tables:
            string_to_sign += request.get_header('x-ms-date') + NEW_LINE
        else:
            string_to_sign += NEW_LINE

        for field in ['If-modified-since', 'If-match', 'If-none-match', 'If-unmodified-since', 'Range']:
            if request.get_header(field) is not None:
                string_to_sign += request.get_header(field)
            string_to_sign += NEW_LINE
        
        # Canonicalized headers
        if not for_tables:
            string_to_sign += canonicalized_headers + NEW_LINE
        
        # Canonicalized resource
        string_to_sign +=  "/" + self._account + path
        for key, value in parse_qs(query).iteritems():
            string_to_sign += NEW_LINE
            string_to_sign += key + ":" + value[0]
        
        request.add_header('Authorization', 'SharedKey ' + self._account + ':'
            + base64.encodestring(hmac.new(self._key,
            unicode(string_to_sign).encode("utf-8"),
            hashlib.sha256).digest()).strip())
        return request

    def sign_request(self, request, use_path_style_uris = None):
        return self._sign_request_impl(request, use_path_style_uris)

    def sign_table_request(self, request, use_path_style_uris = None):
        return self._sign_request_impl(request, for_tables = True,
            use_path_style_uris = use_path_style_uris)


class BlobSharedAccessSignature(object):
    def __init__(self, account_name, account_key):
        self._account = account_name
        self._key = base64.decodestring(account_key)

    def create_signature(self, container, path, resource='b', permissions='r',
                         start='', expiry='', identifier=''):
        canonicalized_name = '/' + self._account + '/' + container + '/' + path
        data_to_sign = [
            permissions,
            start,
            expiry,
            canonicalized_name,
            identifier
        ]
        string_to_sign = NEW_LINE.join(data_to_sign)
        return base64.encodestring(hmac.new(self._key,
                                            unicode(string_to_sign).encode("utf-8"),
                                            hashlib.sha256).digest()).strip()

    def create_signed_qs(self, container, path, resource='b', permissions='r',
                         start='', expiry='', identifier=''):
        if not expiry:
            expiry = (datetime.datetime.utcnow() + datetime.timedelta(minutes=55)).isoformat()[:19] + 'Z'
        params = {
            # The permissions associated with the Shared Access Signature. (read)
            'sp': permissions,
            # The time at which the Shared Access Signature becomes valid.
            'ss': start,
            # The time at which the Shared Access Signature becomes invalid.
            'se': expiry,
            # signedresource. Specify b to designate access scope to the content
            # and metadata of a specific blob in the container.
            'sr': resource,
            'sig': self.create_signature(container, path, resource, permissions, start, expiry, identifier)
        }
        if identifier:
            # A unique value that correlates to an access policy specified at the container level.
            # The signed identifier may have a maximum size of 64 characters.
            params['si'] = identifier
        return urllib.urlencode(params)


class Storage(object):
    CLOUD_HOST = None
    DEVSTORE_HOST = None
    
    def __init__(self, account_name, secret_key, use_path_style_uris):
        if account_name:        
            self.account = account_name
            self.key = secret_key
        else:
            # Devstore
            self.account = "devstoreaccount1"
            self.key = "Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw=="
        self.credentials = StorageSharedKeyCredentials(self.account, self.key)
        
        if use_path_style_uris is None:
            use_path_style_uris = re.match(r'^[^:]*[\d:]+$', self._host)
        self.use_path_style_uris = use_path_style_uris
    
    @property
    def host(self):
        return self.CLOUD_HOST if self.account else self.DEVSTORE_HOST

    @property
    def base_url(self):
        if self.use_path_style_uris:
            return "http://%s/%s" % (self.host, self.account)
        else:
            return "http://%s.%s" % (self.account, self.host)
    
    def create_data_connection_string(self):
        if self.account:
            return u'DefaultEndpointsProtocol=https;AccountName=%s;AccountKey=%s' % (self.account, self.key)
        else:
            return u'UseDevelopmentStorage=true'


# Real Storage Implementations
################################################################################
from blob import BlobStorage
from table import TableStorage
from queue import QueueStorage