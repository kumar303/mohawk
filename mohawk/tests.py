from unittest import TestCase

from nose.tools import eq_

from . import Receiver, Sender
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

        # This callable might be replaced by tests.
        def seen_nonce(nonce, ts):
            return False
        self.seen_nonce = seen_nonce

    def credentials_map(self, id):
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


class TestSender(Base):

    def setUp(self):
        super(TestSender, self).setUp()
        self.url = 'http://site.com/foo?bar=1'

    def Sender(self, method='GET', **kw):
        credentials = kw.pop('credentials', self.credentials)
        sender = Sender(credentials, self.url, method, **kw)
        return sender

    def receive(self, request_header, url=None, method='GET', **kw):
        credentials_map = kw.pop('credentials_map', self.credentials_map)
        kw.setdefault('seen_nonce', self.seen_nonce)
        return Receiver(credentials_map, request_header,
                        url or self.url, method, **kw)

    def test_get_ok(self):
        method = 'GET'
        sn = self.Sender(method=method)
        self.receive(sn.request_header, method=method)

    def test_post_ok(self):
        method = 'POST'
        sn = self.Sender(method=method)
        self.receive(sn.request_header, method=method)

    def test_post_content_ok(self):
        method = 'POST'
        content = 'foo=bar&baz=2'
        sn = self.Sender(method=method, content=content)
        self.receive(sn.request_header, method=method, content=content)

    def test_post_content_type_ok(self):
        method = 'POST'
        content = '{"bar": "foobs"}'
        content_type = 'application/json'
        sn = self.Sender(method=method, content=content,
                         content_type=content_type)
        self.receive(sn.request_header, method=method, content=content,
                     content_type=content_type)

    def test_tamper_with_host(self):
        sn = self.Sender()
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header, url='http://TAMPERED-WITH.com')

    def test_tamper_with_method(self):
        sn = self.Sender(method='GET')
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header, method='POST')

    def test_tamper_with_path(self):
        sn = self.Sender()
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header,
                         url='http://site.com/TAMPERED?bar=1')

    def test_tamper_with_query(self):
        sn = self.Sender()
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header,
                         url='http://site.com/foo?bar=TAMPERED')

    def test_tamper_with_scheme(self):
        sn = self.Sender()
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header, url='https://site.com/foo?bar=1')

    def test_tamper_with_port(self):
        sn = self.Sender()
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header,
                         url='http://site.com:8000/foo?bar=1')

    def test_tamper_with_content(self):
        sn = self.Sender(method='POST')
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header, content='stuff=nope')

    def test_tamper_with_content_type(self):
        sn = self.Sender(method='POST')
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header, content_type='application/json')

    def test_nonce_fail(self):

        def seen_nonce(nonce, ts):
            return True

        sn = self.Sender()

        with self.assertRaises(AlreadyProcessed):
            self.receive(sn.request_header,
                         seen_nonce=seen_nonce)

    def test_nonce_ok(self):

        def seen_nonce(nonce, ts):
            return False

        sn = self.Sender(seen_nonce=seen_nonce)
        self.receive(sn.request_header)

    def test_expired_ts(self):
        sn = self.Sender(_timestamp=utc_now() - 120)
        with self.assertRaises(TokenExpired):
            self.receive(sn.request_header)

    def test_hash_tampering(self):
        sn = self.Sender()
        header = sn.request_header.replace('hash="', 'hash="nope')
        with self.assertRaises(MisComputedContentHash):
            self.receive(header)

    def test_bad_secret(self):
        cfg = {
            'id': 'my-hawk-id',
            'key': 'INCORRECT; YOU FAIL',
            'algorithm': 'sha256',
        }
        sn = self.Sender(credentials=cfg)
        with self.assertRaises(MacMismatch):
            self.receive(sn.request_header)

    def test_unexpected_algorithm(self):
        cr = self.credentials.copy()
        cr['algorithm'] = 'sha512'
        sn = self.Sender(credentials=cr)

        with self.assertRaises(MacMismatch):
            # Validate with a credentials using sha256.
            self.receive(sn.request_header)

    def test_invalid_credentials(self):
        cfg = self.credentials.copy()
        # Create an invalid credentials.
        del cfg['algorithm']

        with self.assertRaises(InvalidCredentials):
            self.Sender(credentials=cfg)

    def test_unknown_id(self):
        cr = self.credentials.copy()
        cr['id'] = 'someone-else'
        sn = self.Sender(credentials=cr)

        with self.assertRaises(CredentialsLookupError):
            self.receive(sn.request_header)

    def test_bad_ext(self):
        sn = self.Sender(ext='my external data')

        header = sn.request_header.replace('my external data', 'TAMPERED')
        with self.assertRaises(MacMismatch):
            self.receive(header)

    def test_ext_with_quotes(self):
        sn = self.Sender(ext='quotes=""')
        self.receive(sn.request_header)
        parsed = parse_authorization_header(sn.request_header)
        eq_(parsed['ext'], 'quotes=""')

    def test_ext_with_new_line(self):
        sn = self.Sender(ext="new line \n in the middle")
        self.receive(sn.request_header)
        parsed = parse_authorization_header(sn.request_header)
        eq_(parsed['ext'], "new line \n in the middle")

    def test_ext_with_illegal_chars(self):
        with self.assertRaises(BadHeaderValue):
            self.Sender(ext="something like \t is illegal")

    def test_ext_with_illegal_unicode(self):
        with self.assertRaises(BadHeaderValue):
            self.Sender(ext=u'Ivan Kristi\u0107')

    def test_ext_with_illegal_utf8(self):
        with self.assertRaises(BadHeaderValue):
            self.Sender(ext=u'Ivan Kristi\u0107'.encode('utf8'))

    def test_app_ok(self):
        app = 'custom-app'
        sn = self.Sender(app=app)
        self.receive(sn.request_header)
        parsed = parse_authorization_header(sn.request_header)
        eq_(parsed['app'], app)

    def test_tampered_app(self):
        app = 'custom-app'
        sn = self.Sender(app=app)
        header = sn.request_header.replace(app, 'TAMPERED-WITH')
        with self.assertRaises(MacMismatch):
            self.receive(header)

    def test_dlg_ok(self):
        dlg = 'custom-dlg'
        sn = self.Sender(dlg=dlg)
        self.receive(sn.request_header)
        parsed = parse_authorization_header(sn.request_header)
        eq_(parsed['dlg'], dlg)

    def test_tampered_dlg(self):
        dlg = 'custom-dlg'
        sn = self.Sender(dlg=dlg, app='some-app')
        header = sn.request_header.replace(dlg, 'TAMPERED-WITH')
        with self.assertRaises(MacMismatch):
            self.receive(header)


class TestReceiver(Base):

    def setUp(self):
        super(TestReceiver, self).setUp()
        self.url = 'http://site.com/'
        self.sender = None
        self.receiver = None

    def receive(self, method='GET', **kw):
        url = kw.pop('url', self.url)
        sender = kw.pop('sender', None)
        sender_kw = kw.pop('sender_kw', {})
        sender_url = kw.pop('sender_url', url)

        credentials_map = kw.pop('credentials_map',
                                 lambda id: self.credentials)

        if sender:
            self.sender = sender
        else:
            self.sender = Sender(self.credentials, sender_url, method,
                                 **sender_kw)

        self.receiver = Receiver(credentials_map,
                                 self.sender.request_header, url, method,
                                 **kw)

    def respond(self, **kw):
        accept_kw = kw.pop('accept_kw', {})
        receiver = kw.pop('receiver', self.receiver)

        receiver.respond(**kw)
        self.sender.accept_response(receiver.response_header, **accept_kw)

        return receiver.response_header

    def test_invalid_credentials_lookup(self):
        with self.assertRaises(InvalidCredentials):
            # Return invalid credentials.
            self.receive(credentials_map=lambda *a: {})

    def test_get_ok(self):
        method = 'GET'
        self.receive(method=method)
        self.respond()

    def test_post_ok(self):
        method = 'POST'
        self.receive(method=method)
        self.respond()

    def test_respond_with_wrong_content(self):
        self.receive()
        with self.assertRaises(MacMismatch):
            self.respond(content='real content',
                         accept_kw=dict(content='TAMPERED WITH'))

    def test_respond_with_wrong_content_type(self):
        self.receive()
        with self.assertRaises(MacMismatch):
            self.respond(content_type='text/html',
                         accept_kw=dict(content_type='application/json'))

    def test_respond_with_wrong_url(self):
        self.receive(url='http://fakesite.com')
        wrong_receiver = self.receiver

        self.receive(url='http://realsite.com')

        with self.assertRaises(MacMismatch):
            self.respond(receiver=wrong_receiver)

    def test_respond_with_wrong_method(self):
        self.receive(method='GET')
        wrong_receiver = self.receiver

        self.receive(method='POST')

        with self.assertRaises(MacMismatch):
            self.respond(receiver=wrong_receiver)

    def test_receive_wrong_method(self):
        self.receive(method='GET')
        wrong_sender = self.sender

        with self.assertRaises(MacMismatch):
            self.receive(method='POST',
                         sender=wrong_sender)

    def test_receive_wrong_url(self):
        self.receive(url='http://fakesite.com/')
        wrong_sender = self.sender

        with self.assertRaises(MacMismatch):
            self.receive(url='http://realsite.com/',
                         sender=wrong_sender)

    def test_receive_wrong_content(self):
        self.receive(sender_kw=dict(content='real request'),
                     content='real request')
        wrong_sender = self.sender

        with self.assertRaises(MacMismatch):
            self.receive(content='TAMPERED WITH',
                         sender=wrong_sender)

    def test_receive_wrong_content_type(self):
        self.receive(sender_kw=dict(content_type='text/html'),
                     content_type='text/html')
        wrong_sender = self.sender

        with self.assertRaises(MacMismatch):
            self.receive(content_type='application/json',
                         sender=wrong_sender)


class TestSendAndReceive(Base):

    def test(self):
        credentials = {
            'id': 'some-id',
            'key': 'some secret',
            'algorithm': 'sha256'
        }

        url = 'https://my-site.com/'
        method = 'POST'

        # The client sends a request with a Hawk header.
        content = 'foo=bar&baz=nooz'
        content_type = 'application/x-www-form-urlencoded'

        sender = Sender(credentials,
                        url, method,
                        content=content,
                        content_type=content_type)

        # The server receives a request and authorizes access.
        receiver = Receiver(lambda id: credentials,
                            sender.request_header,
                            url, method,
                            content=content,
                            content_type=content_type)

        # The server responds with a similar Hawk header.
        content = 'we are friends'
        content_type = 'text/plain'
        receiver.respond(content=content,
                         content_type=content_type)

        # The client receives a response and authorizes access.
        sender.accept_response(receiver.response_header,
                               content=content,
                               content_type=content_type)
