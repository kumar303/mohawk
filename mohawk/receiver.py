import logging

from .base import HawkAuthority, Resource
from .exc import CredentialsLookupError
from .util import (calculate_mac,
                   parse_authorization_header,
                   validate_credentials)

__all__ = ['Receiver']
log = logging.getLogger(__name__)


class Receiver(HawkAuthority):

    def __init__(self,
                 credentials_map,
                 request_header,
                 url,
                 method,
                 content='',
                 content_type='text/plain',
                 seen_nonce=None,
                 **auth_kw):

        self.response_header = None  # make into property that can raise exc?
        self.credentials_map = credentials_map
        self.seen_nonce = seen_nonce

        log.debug('accepting request {header}'.format(header=request_header))

        parsed_header = parse_authorization_header(request_header)

        try:
            credentials = self.credentials_map(parsed_header['id'])
        except LookupError, exc:
            log.debug('Catching {0.__class__.__name__}: {0}'.format(exc))
            raise CredentialsLookupError(
                'Could not find credentials for ID {0}'
                .format(parsed_header['id']))
        validate_credentials(credentials)

        resource = Resource(url=url,
                            method=method,
                            ext=parsed_header.get('ext', None),
                            app=parsed_header.get('app', None),
                            dlg=parsed_header.get('dlg', None),
                            credentials=credentials,
                            nonce=parsed_header['nonce'],
                            seen_nonce=self.seen_nonce,
                            content=content,
                            timestamp=parsed_header['ts'],
                            content_type=content_type)

        self._authorize('header', parsed_header, resource, **auth_kw)

        # Now that we verified an incoming request, we can re-use some of its
        # properties to build our response header.

        self.parsed_header = parsed_header
        self.resource = resource

    def respond(self,
                content='',
                content_type='text/plain',
                ext=None):

        log.debug('generating response header')

        resource = Resource(url=self.resource.url,
                            credentials=self.resource.credentials,
                            ext=ext,
                            app=self.parsed_header.get('app', None),
                            dlg=self.parsed_header.get('dlg', None),
                            nonce=self.parsed_header['nonce'],
                            method=self.resource.method,
                            content=content,
                            content_type=content_type)

        mac = calculate_mac('response', resource)

        self.response_header = self._make_header(resource, mac)
        return self.response_header
