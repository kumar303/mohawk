from unittest import TestCase

from nose.tools import eq_

from . import Client, Server
from .exc import (AlreadyProcessed,
                  BadHeaderValue,
                  CredentialsLookupError,
                  InvalidCredentials,
                  MacMismatch,
                  MisComputedContentHash,
                  TokenExpired)
from .util import (parse_authorization_header,
                   utc_now,
                   validate_credentials)


class Base(TestCase):

    def setUp(self):
        self.credentials = {
            'id': 'my-hawk-id',
            'key': 'my hAwK sekret',
            'algorithm': 'sha256',
        }
        self._credentials_lookup_callable = None

        # This callable might be replaced by tests.
        def seen_nonce(nonce, ts):
            return False
        self._seen_nonce = seen_nonce

        self.client = Client(self.credentials,
                             seen_nonce=lambda *a: self._seen_nonce(*a))
        self.server = Server(self.credentials_lookup,
                             seen_nonce=lambda *a: self._seen_nonce(*a))

    def credentials_lookup(self, id):
        if self._credentials_lookup_callable:
            return self._credentials_lookup_callable(id)

        # Pretend this is doing something more interesting like looking up
        # a credentials by ID in a database.
        if self.credentials['id'] != id:
            raise LookupError('No credentialsuration for Hawk ID {id}'
                              .format(id=id))
        return self.credentials


class TestConfig(Base):

    def test_no_id(self):
        c = self.credentials.copy()
        del c['id']
        with self.assertRaises(InvalidCredentials):
            validate_credentials(c)

    def test_no_key(self):
        c = self.credentials.copy()
        del c['key']
        with self.assertRaises(InvalidCredentials):
            validate_credentials(c)

    def test_no_algo(self):
        c = self.credentials.copy()
        del c['algorithm']
        with self.assertRaises(InvalidCredentials):
            validate_credentials(c)

    def test_no_credentials(self):
        with self.assertRaises(InvalidCredentials):
            validate_credentials(None)


class TestClient(Base):

    def setUp(self):
        super(TestClient, self).setUp()
        self.url = 'http://site.com/foo?bar=1'

    def header(self, method='GET', **kw):
        credentials = kw.pop('credentials', None)
        if credentials:
            self.client.reconfigure(credentials)
        return self.client.header(self.url, method, **kw)['header']

    def authenticate(self, header, url=None, method='GET', **kw):
        self.server.authenticate(header, url or self.url, method,
                                 **kw)

    def test_get_ok(self):
        method = 'GET'
        header = self.header(method=method)
        self.authenticate(header, method=method)

    def test_post_ok(self):
        method = 'POST'
        header = self.header(method=method)
        self.authenticate(header, method=method)

    def test_post_content_ok(self):
        method = 'POST'
        content = 'foo=bar&baz=2'
        header = self.header(method=method, content=content)
        self.authenticate(header, method=method, content=content)

    def test_post_content_type_ok(self):
        method = 'POST'
        content = '{"bar": "foobs"}'
        content_type = 'application/json'
        header = self.header(method=method, content=content,
                             content_type=content_type)
        self.authenticate(header, method=method, content=content,
                          content_type=content_type)

    def test_tamper_with_host(self):
        header = self.header()
        with self.assertRaises(MacMismatch):
            self.authenticate(header, url='http://TAMPERED-WITH.com')

    def test_tamper_with_method(self):
        header = self.header(method='GET')
        with self.assertRaises(MacMismatch):
            self.authenticate(header, method='POST')

    def test_tamper_with_path(self):
        header = self.header()
        with self.assertRaises(MacMismatch):
            self.authenticate(header, url='http://site.com/TAMPERED?bar=1')

    def test_tamper_with_query(self):
        header = self.header()
        with self.assertRaises(MacMismatch):
            self.authenticate(header, url='http://site.com/foo?bar=TAMPERED')

    def test_tamper_with_scheme(self):
        header = self.header()
        with self.assertRaises(MacMismatch):
            self.authenticate(header, url='https://site.com/foo?bar=1')

    def test_tamper_with_port(self):
        header = self.header()
        with self.assertRaises(MacMismatch):
            self.authenticate(header, url='http://site.com:8000/foo?bar=1')

    def test_tamper_with_content(self):
        header = self.header(method='POST')
        with self.assertRaises(MacMismatch):
            self.authenticate(header, content='stuff=nope')

    def test_tamper_with_content_type(self):
        header = self.header(method='POST')
        with self.assertRaises(MacMismatch):
            self.authenticate(header, content_type='application/json')

    def test_nonce_fail(self):
        header = self.header()

        def seen_nonce(nonce, ts):
            return True
        self._seen_nonce = seen_nonce

        with self.assertRaises(AlreadyProcessed):
            self.authenticate(header)

    def test_nonce_ok(self):
        header = self.header()

        def seen_nonce(nonce, ts):
            return False
        self._seen_nonce = seen_nonce

        self.authenticate(header)

    def test_expired_ts(self):
        header = self.header(_timestamp=utc_now() - 120)
        with self.assertRaises(TokenExpired):
            self.authenticate(header)

    def test_hash_tampering(self):
        header = self.header()
        header = header.replace('hash="', 'hash="nope')
        with self.assertRaises(MisComputedContentHash):
            self.authenticate(header)

    def test_bad_secret(self):
        cfg = {
            'id': 'my-hawk-id',
            'key': 'INCORRECT; YOU FAIL',
            'algorithm': 'sha256',
        }
        header = self.header(credentials=cfg)
        with self.assertRaises(MacMismatch):
            self.authenticate(header)

    def test_unexpected_algorithm(self):
        cfg = self.credentials.copy()
        cfg['algorithm'] = 'sha512'
        header = self.header(credentials=cfg)

        with self.assertRaises(MacMismatch):
            # Validate with a credentials using sha256.
            self.authenticate(header)

    def test_invalid_credentials(self):
        cfg = self.credentials.copy()
        # Create an invalid credentials.
        del cfg['algorithm']

        with self.assertRaises(InvalidCredentials):
            self.header(credentials=cfg)

    def test_unknown_id(self):
        cfg = self.credentials.copy()
        cfg['id'] = 'someone-else'
        header = self.header(credentials=cfg)

        with self.assertRaises(CredentialsLookupError):
            self.authenticate(header)

    def test_bad_ext(self):
        header = self.header(ext='my external data')

        header = header.replace('my external data', 'TAMPERED')
        with self.assertRaises(MacMismatch):
            self.authenticate(header)

    def test_ext_with_quotes(self):
        header = self.header(ext='quotes=""')
        self.authenticate(header)
        parsed = parse_authorization_header(header)
        eq_(parsed['ext'], 'quotes=""')

    def test_ext_with_new_line(self):
        header = self.header(ext="new line \n in the middle")
        self.authenticate(header)
        parsed = parse_authorization_header(header)
        eq_(parsed['ext'], "new line \n in the middle")

    def test_ext_with_illegal_chars(self):
        with self.assertRaises(BadHeaderValue):
            self.header(ext="something like \t is illegal")

    def test_ext_with_illegal_unicode(self):
        with self.assertRaises(BadHeaderValue):
            self.header(ext=u'Ivan Kristi\u0107')

    def test_ext_with_illegal_utf8(self):
        with self.assertRaises(BadHeaderValue):
            self.header(ext=u'Ivan Kristi\u0107'.encode('utf8'))

    def test_app_ok(self):
        app = 'custom-app'
        header = self.header(app=app)
        self.authenticate(header)
        parsed = parse_authorization_header(header)
        eq_(parsed['app'], app)

    def test_tampered_app(self):
        app = 'custom-app'
        header = self.header(app=app)
        header = header.replace(app, 'TAMPERED-WITH')
        with self.assertRaises(MacMismatch):
            self.authenticate(header)

    def test_dlg_ok(self):
        dlg = 'custom-dlg'
        header = self.header(dlg=dlg)
        self.authenticate(header)
        parsed = parse_authorization_header(header)
        eq_(parsed['dlg'], dlg)

    def test_tampered_dlg(self):
        dlg = 'custom-dlg'
        header = self.header(dlg=dlg, app='some-app')
        header = header.replace(dlg, 'TAMPERED-WITH')
        with self.assertRaises(MacMismatch):
            self.authenticate(header)


class TestServer(Base):

    def setUp(self):
        super(TestServer, self).setUp()
        self.url = 'http://site.com/'

    def receive_request(self, method='GET', **kw):
        url = kw.pop('url', self.url)
        header = self.client.header(url, method, **kw)['header']
        self.server.authenticate(header, url, method)

    def outgoing_header(self, **kw):
        return self.server.header(**kw)

    def authenticate(self, header, **kw):
        credentials = kw.pop('credentials', None)
        if credentials:
            self.client.recredentialsure(credentials)
        self.client.authenticate(header, **kw)

    def test_invalid_credentials_lookup(self):
        # Return an invalid credentials.
        self._credentials_lookup_callable = lambda *a: {}

        with self.assertRaises(InvalidCredentials):
            self.receive_request()

    def test_get_ok(self):
        method = 'GET'
        self.receive_request(method=method)
        header = self.outgoing_header()
        self.authenticate(header)

    def test_post_ok(self):
        method = 'POST'
        self.receive_request(method=method)
        header = self.outgoing_header()
        self.authenticate(header)

    def test_wrong_method(self):
        self.receive_request(method='GET')
        bad_header = self.outgoing_header()

        # Reset header cache.
        self.receive_request(method='POST')

        with self.assertRaises(MacMismatch):
            self.authenticate(bad_header)

    def test_pass_a_trusted_request(self):
        method = 'POST'
        header = self.client.header(url=self.url, method=method)['header']
        serv = Server(self.credentials_lookup)
        serv.authenticate(url=self.url, method=method, header=header)

        header = self.outgoing_header(trusted_request=serv.trusted_request)
        self.authenticate(header)

    def test_require_incoming_header(self):
        with self.assertRaises(NotImplementedError):
            self.outgoing_header()

    def test_content_tampering(self):
        self.receive_request()
        header = self.outgoing_header(content='real content')

        with self.assertRaises(MacMismatch):
            self.authenticate(header, content='TAMPERED WITH')

    def test_content_type_tampering(self):
        self.receive_request()
        header = self.outgoing_header(content_type='text/html')

        with self.assertRaises(MacMismatch):
            self.authenticate(header, content_type='application/json')

    def test_url_does_not_match_request(self):
        self.receive_request(url='http://fakesite.com/')
        bad_header = self.outgoing_header()

        # Reset header cache.
        self.receive_request(url='http://realsite.com/')

        with self.assertRaises(MacMismatch):
            self.authenticate(bad_header)


class TestClientAndServer(Base):

    def test_integration(self):
        credentials = {
            'id': 'some-id',
            'key': 'some secret',
            'algorithm': 'sha256'
        }

        url = 'https://my-site.com/'
        method = 'POST'

        client = Client(credentials)
        server = Server(lambda *a: credentials)

        # The client makes a request with a Hawk header.
        content = 'foo=bar&baz=nooz'
        content_type = 'application/x-www-form-urlencoded'
        request_hdr = client.header(url, method,
                                    content=content,
                                    content_type=content_type)

        # The server receives and authenticates the response.
        server.authenticate(request_hdr['header'], url, method,
                            content=content,
                            content_type=content_type)

        # The server responds with a similar Hawk header.
        content = 'we are friends'
        content_type = 'text/plain'
        response_hdr = server.header(content=content,
                                     content_type=content_type)

        # The client receives and authenticates the response.
        client.authenticate(response_hdr,
                            content=content,
                            content_type=content_type)
