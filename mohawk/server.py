import logging

from .base import HawkAuthority, Resource
from .exc import ConfigLookupError
from .util import (calculate_mac,
                   parse_authorization_header,
                   validate_config)

log = logging.getLogger(__name__)


class Server(HawkAuthority):

    def __init__(self, config_map, seen_nonce=None):
        self.config_map = config_map
        self.trusted_request = None
        self.seen_nonce = seen_nonce

    def authenticate(self,
                     header,
                     url,
                     method,
                     content='',
                     content_type='text/plain',
                     **auth_kw):
        log.debug('authenticating {header}'.format(header=header))

        parsed_header = parse_authorization_header(header)

        try:
            credentials = self.config_map(parsed_header['id'])
        except LookupError, exc:
            log.debug('Catching {0.__class__.__name__}: {0}'.format(exc))
            raise ConfigLookupError('Could not find credentials for ID {0}'
                                    .format(parsed_header['id']))
        validate_config(credentials)

        resource = Resource(url=url,
                            method=method,
                            ext=parsed_header.get('ext', None),
                            app=parsed_header.get('app', None),
                            dlg=parsed_header.get('dlg', None),
                            config=credentials,
                            nonce=parsed_header['nonce'],
                            seen_nonce=self.seen_nonce,
                            content=content,
                            timestamp=parsed_header['ts'],
                            content_type=content_type)

        self._authenticate('header', parsed_header, resource, **auth_kw)

        # Now that we verified an incoming request, we can re-use some of its
        # properties to build our response header.
        self.trusted_request = {'header': parsed_header,
                                'resource': resource}

    def header(self,
               content='',
               content_type='text/plain',
               trusted_request=None):
        """
        Generate a Server-Authorization header for a given response.
        """
        log.debug('generating response header')
        if trusted_request:
            self.trusted_request = trusted_request
        if not self.trusted_request:
            raise NotImplementedError(
                    'cannot build a response header without having already '
                    'authenticated an incoming request. This can be fixed by '
                    'adding some extra parameters')

        trusted = self.trusted_request

        resource = Resource(url=trusted['resource'].url,
                            config=trusted['resource'].config,
                            ext=trusted['header'].get('ext', None),
                            app=trusted['header'].get('app', None),
                            dlg=trusted['header'].get('dlg', None),
                            nonce=trusted['header']['nonce'],
                            method=trusted['resource'].method,
                            content=content,
                            content_type=content_type)

        mac = calculate_mac('response', resource)
        return self._make_header(resource, mac)
