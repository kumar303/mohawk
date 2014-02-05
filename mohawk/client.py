import logging

from .base import HawkAuthority, Resource
from .util import calculate_mac, parse_authorization_header, validate_config

__all__ = ['Client']
log = logging.getLogger(__name__)


class Client(HawkAuthority):

    def __init__(self, config, seen_nonce=None):
        self.reconfigure(config)
        self.request_header = None
        self.seen_nonce = seen_nonce

    def reconfigure(self, config):
        validate_config(config)
        self.config = config

    def authenticate(self,
                     response_header,
                     content='',
                     content_type='text/plain',
                     request_header=None,
                     **auth_kw):
        log.debug('authenticating {header}'.format(header=response_header))

        if request_header:
            self.request_header = request_header
        if not self.request_header:
            raise NotImplementedError(
                    'cannot authenticate a response header without first '
                    'generating a request header')

        parsed_header = parse_authorization_header(response_header)

        resource = Resource(url=self.request_header['resource'].url,
                            method=self.request_header['resource'].method,
                            ext=parsed_header.get('ext', None),
                            app=parsed_header.get('app', None),
                            dlg=parsed_header.get('dlg', None),
                            config=self.config,
                            nonce=parsed_header['nonce'],
                            seen_nonce=self.seen_nonce,
                            content=content,
                            timestamp=parsed_header['ts'],
                            content_type=content_type)

        self._authenticate('response', parsed_header, resource, **auth_kw)

    def header(self,
               url,
               method,
               content='',
               content_type='text/plain',
               nonce=None,
               ext=None,
               app=None,
               dlg=None,
               _timestamp=None):
        """
        Construct an Authorization header for a request.

        :param url: 'http://example.com/resource?a=b'
        :param method: HTTP verb ('GET', 'POST', etc)
        """
        log.debug('generating request header')
        resource = Resource(url=url,
                            config=self.config,
                            ext=ext,
                            app=app,
                            dlg=dlg,
                            nonce=nonce,
                            method=method,
                            content=content,
                            timestamp=_timestamp,
                            content_type=content_type)

        mac = calculate_mac('header', resource)
        self.request_header = {'header': self._make_header(resource, mac),
                               'resource': resource}
        return self.request_header
