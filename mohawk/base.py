import logging
import math
import pprint
from urlparse import urlparse

from .exc import (AlreadyProcessed,
                  MacMismatch,
                  MisComputedContentHash,
                  TokenExpired)
from .util import (calculate_mac,
                   calculate_payload_hash,
                   prepare_header_val,
                   random_string,
                   strings_match,
                   utc_now)

default_ts_skew_in_seconds = 60
log = logging.getLogger(__name__)


class HawkAuthority:

    def _authorize(self, mac_type, parsed_header, resource,
                   their_timestamp=None,
                   timestamp_skew_in_seconds=default_ts_skew_in_seconds,
                   localtime_offset_in_seconds=0):

        now = utc_now(offset_in_seconds=localtime_offset_in_seconds)

        mac = calculate_mac(mac_type, resource)
        if not strings_match(mac, parsed_header['mac']):
            raise MacMismatch('MACs do not match; ours: {ours}; '
                              'theirs: {theirs}'
                              .format(ours=mac, theirs=parsed_header['mac']))

        # TODO: if content is empty should we be less strict and allow
        # an empty hash attribute in the header?
        p_hash = calculate_payload_hash(resource.content,
                                        resource.credentials['algorithm'],
                                        resource.content_type)
        if not strings_match(p_hash, parsed_header['hash']):
            # The hash declared in the header is incorrect.
            # Content could have been tampered with.
            log.debug('mismatched content: {content}'
                      .format(content=repr(resource.content)))
            log.debug('mismatched content-type: {typ}'
                      .format(typ=repr(resource.content_type)))
            raise MisComputedContentHash(
                'Our hash {ours} ({algo}) did not '
                'match theirs {theirs}'
                .format(ours=p_hash,
                        theirs=parsed_header['hash'],
                        algo=resource.credentials['algorithm']))

        if resource.seen_nonce:
            if resource.seen_nonce(parsed_header['nonce'],
                                   parsed_header['ts']):
                raise AlreadyProcessed('Nonce {nonce} with timestamp {ts} '
                                       'has already been processed'
                                       .format(nonce=parsed_header['nonce'],
                                               ts=parsed_header['ts']))
        else:
            log.warn('seen_nonce was None; not checking nonce. '
                     'You may be vulnerable to replay attacks')

        their_ts = int(their_timestamp or parsed_header['ts'])

        if math.fabs(their_ts - now) > timestamp_skew_in_seconds:
            raise TokenExpired('token with UTC timestamp {ts} has expired; '
                               'compared to {now}'
                               .format(ts=their_ts, now=now),
                               localtime_in_seconds=now)

        log.debug('authorized OK')

    def _make_header(self, resource, mac, additional_keys=None):
        keys = additional_keys
        if not keys:
            # These are the default header keys that you'd send with a
            # request header. Response headers are odd because they
            # exclude a bunch of keys.
            keys = ('id', 'ts', 'nonce', 'ext', 'app', 'dlg')

        header = u'Hawk mac="{mac}", hash="{hash}"'.format(
            mac=prepare_header_val(mac),
            hash=prepare_header_val(resource.content_hash))

        if 'id' in keys:
            header = u'{header}, id="{id}"'.format(
                header=header,
                id=prepare_header_val(resource.credentials['id']))

        if 'ts' in keys:
            header = u'{header}, ts="{ts}"'.format(
                header=header, ts=prepare_header_val(resource.timestamp))

        if 'nonce' in keys:
            header = u'{header}, nonce="{nonce}"'.format(
                header=header, nonce=prepare_header_val(resource.nonce))

        # These are optional so we need to check if they have values first.

        if 'ext' in keys and resource.ext:
            header = u'{header}, ext="{ext}"'.format(
                header=header, ext=prepare_header_val(resource.ext))

        if 'app' in keys and resource.app:
            header = u'{header}, app="{app}"'.format(
                header=header, app=prepare_header_val(resource.app))

        if 'dlg' in keys and resource.dlg:
            header = u'{header}, dlg="{dlg}"'.format(
                header=header, dlg=prepare_header_val(resource.dlg))

        # Use UTF8 for sanity even though the validator (currently)
        # rejects non-ascii.
        header = header.encode('utf8')

        log.debug('Hawk header for URL={url} method={method}: {header}'
                  .format(url=resource.url, method=resource.method,
                          header=header))
        return header


class Resource:
    """
    Normalized request/response resource.
    """

    def __init__(self, **kw):
        self.credentials = kw.pop('credentials')
        self.method = kw.pop('method').upper()
        self.content = kw.pop('content')
        self.content_type = kw.pop('content_type')
        self.ext = kw.pop('ext', None)
        self.app = kw.pop('app', None)
        self.dlg = kw.pop('dlg', None)

        self.content_hash = calculate_payload_hash(
            self.content, self.credentials['algorithm'],
            self.content_type)

        self.timestamp = str(kw.pop('timestamp', None) or utc_now())

        self.nonce = kw.pop('nonce', None)
        if not self.nonce:
            self.nonce = random_string(6)

        # This is a lookup function for checking nonces.
        self.seen_nonce = kw.pop('seen_nonce', None)

        self.url = kw.pop('url')
        if not self.url:
            raise ValueError('url was empty')
        url_parts = self.parse_url(self.url)
        log.debug('parsed URL parts: \n{parts}'
                  .format(parts=pprint.pformat(url_parts)))

        self.name = url_parts['resource'] or ''
        self.host = url_parts['hostname'] or ''
        self.port = str(url_parts['port'])

        if kw.keys():
            raise TypeError('Unknown keyword argument(s): {0}'
                            .format(kw.keys()))

    def parse_url(self, url):
        url_parts = urlparse(url)
        url_dict = {
            'scheme': url_parts.scheme,
            'hostname': url_parts.hostname,
            'port': url_parts.port,
            'path': url_parts.path,
            'resource': url_parts.path,
            'query': url_parts.query,
        }
        if len(url_dict['query']) > 0:
            url_dict['resource'] = '%s?%s' % (url_dict['resource'],
                                              url_dict['query'])

        if url_parts.port is None:
            if url_parts.scheme == 'http':
                url_dict['port'] = 80
            elif url_parts.scheme == 'https':
                url_dict['port'] = 443
        return url_dict
