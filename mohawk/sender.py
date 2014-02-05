import logging

from .base import HawkAuthority, Resource
from .util import (calculate_mac,
                   parse_authorization_header,
                   validate_credentials)

__all__ = ['Sender']
log = logging.getLogger(__name__)


class Sender(HawkAuthority):

    def __init__(self, credentials,
                 url,
                 method,
                 content='',
                 content_type='text/plain',
                 nonce=None,
                 ext=None,
                 app=None,
                 dlg=None,
                 seen_nonce=None,
                 # For easier testing:
                 _timestamp=None):

        self.reconfigure(credentials)
        self.request_header = None
        self.seen_nonce = seen_nonce

        log.debug('generating request header')
        self.req_resource = Resource(url=url,
                                     credentials=self.credentials,
                                     ext=ext,
                                     app=app,
                                     dlg=dlg,
                                     nonce=nonce,
                                     method=method,
                                     content=content,
                                     timestamp=_timestamp,
                                     content_type=content_type)

        mac = calculate_mac('header', self.req_resource)
        self.request_header = self._make_header(self.req_resource, mac)

    def accept_response(self,
                        response_header,
                        content='',
                        content_type='text/plain',
                        **auth_kw):
        log.debug('accepting response {header}'
                  .format(header=response_header))

        parsed_header = parse_authorization_header(response_header)

        resource = Resource(url=self.req_resource.url,
                            method=self.req_resource.method,
                            ext=parsed_header.get('ext', None),
                            app=parsed_header.get('app', None),
                            dlg=parsed_header.get('dlg', None),
                            credentials=self.credentials,
                            nonce=parsed_header['nonce'],
                            seen_nonce=self.seen_nonce,
                            content=content,
                            timestamp=parsed_header['ts'],
                            content_type=content_type)

        self._authorize('response', parsed_header, resource, **auth_kw)

    def reconfigure(self, credentials):
        validate_credentials(credentials)
        self.credentials = credentials
