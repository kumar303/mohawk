from base64 import b64encode, urlsafe_b64encode
import calendar
import hashlib
import hmac
import logging
import math
import os
import pprint
import re
import time

from .exc import BadHeaderValue, HawkFail, InvalidCredentials


HAWK_VER = 1
log = logging.getLogger(__name__)


def validate_credentials(creds):
    if not isinstance(creds, dict):
        raise InvalidCredentials('credentials must be a dict')
    try:
        creds['id']
        creds['key']
        creds['algorithm']
    except KeyError, exc:
        raise InvalidCredentials('{0.__class__.__name__}: {0}'.format(exc))


def random_string(length):
    """Generates a random string for a given length."""
    # this conservatively gets 8*length bits and then returns 6*length of
    # them. Grabbing (6/8)*length bits could lose some entropy off the ends.
    return urlsafe_b64encode(os.urandom(length))[:length]


def calculate_payload_hash(payload, algorithm, content_type):
    """Calculates a hash for a given payload."""
    p_hash = hashlib.new(algorithm)

    parts = []
    parts.append('hawk.' + str(HAWK_VER) + '.payload\n')
    parts.append(parse_content_type(content_type) + '\n')
    parts.append(payload or '')
    parts.append('\n')

    log.debug('calculating payload hash from:\n{parts}'
              .format(parts=pprint.pformat(parts)))

    for p in parts:
        p_hash.update(p)

    return b64encode(p_hash.digest())


def calculate_mac(mac_type, resource, content_hash):
    """Calculates a message authorization code (MAC)."""
    normalized = normalize_string(mac_type, resource, content_hash)
    log.debug('normalized resource for mac calc: {norm}'
              .format(norm=normalized))
    digestmod = getattr(hashlib, resource.credentials['algorithm'])
    result = hmac.new(resource.credentials['key'], normalized, digestmod)
    return b64encode(result.digest())


def normalize_string(mac_type, resource, content_hash):
    """Serializes mac_type and resource into a HAWK string."""

    normalized = [
        'hawk.' + str(HAWK_VER) + '.' + mac_type,
        normalize_header_attr(resource.timestamp),
        normalize_header_attr(resource.nonce),
        normalize_header_attr(resource.method or ''),
        normalize_header_attr(resource.name or ''),
        normalize_header_attr(resource.host),
        normalize_header_attr(resource.port),
        normalize_header_attr(content_hash or '')
    ]

    # The blank lines are important. They follow what the Node Hawk lib does.

    normalized.append(normalize_header_attr(resource.ext or ''))

    if resource.app:
        normalized.append(normalize_header_attr(resource.app))
        normalized.append(normalize_header_attr(resource.dlg or ''))

    # Add trailing new line.
    normalized.append('')

    normalized = '\n'.join(normalized)

    return normalized


def parse_content_type(content_type):
    """Cleans up content_type."""
    if content_type:
        return content_type.split(';')[0].strip().lower()
    else:
        return ''


def parse_authorization_header(auth_header):
    """
    Example Authorization header:

        'Hawk id="dh37fgj492je", ts="1367076201", nonce="NPHgnG", ext="and
        welcome!", mac="CeWHy4d9kbLGhDlkyw2Nh3PJ7SDOdZDa267KH4ZaNMY="'
    """
    allowable_keys = ['id', 'ts', 'nonce', 'hash',
                      'ext', 'mac', 'app', 'dlg']

    attributes = {}
    parts = auth_header.split(',')
    auth_scheme_parts = parts[0].split(' ')
    if not 'hawk' == auth_scheme_parts[0].lower():
        raise HawkFail("Unknown scheme: " + auth_scheme_parts[0].lower())

    # Replace 'Hawk key: value' with 'key: value'
    # which matches the rest of parts
    parts[0] = auth_scheme_parts[1]

    for part in parts:
        attr_parts = part.split('=')
        key = attr_parts[0].strip()
        if key not in allowable_keys:
            raise HawkFail("Unknown Hawk key_" + attr_parts[0] + "_")

        # TODO we don't do a good job of parsing, '=' should work for more =.
        # hash or mac value includes '=' character... fixup
        if len(attr_parts) == 3:
            attr_parts[1] += '=' + attr_parts[2]

        # Chop of quotation marks
        value = attr_parts[1]

        if attr_parts[1].find('"') == 0:
            value = attr_parts[1][1:]

        if value.find('"') > -1:
            value = value[0:-1]

        validate_header_attr(value, name=key)
        value = unescape_header_attr(value)
        attributes[key] = value

    log.debug('parsed Hawk header: {header} into: \n{parsed}'
              .format(header=auth_header, parsed=pprint.pformat(attributes)))
    return attributes


def strings_match(a, b):
    # Constant time string comparision, mitigates side channel attacks.
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0


def utc_now(offset_in_seconds=0.0):
    # TODO: add support for SNTP server? See ntplib module.
    return int(math.floor(calendar.timegm(time.gmtime()) +
                          float(offset_in_seconds)))


# Allowed value characters:
# !#$%&'()*+,-./:;<=>?@[]^_`{|}~ and space, a-z, A-Z, 0-9, \, "
_header_attribute_chars = re.compile(
    r"^[ \w\!#\$%&'\(\)\*\+,\-\./\:;<\=>\?@\[\]\^`\{\|\}~\"\\]*$")


def validate_header_attr(val, name=None):
    if not _header_attribute_chars.match(val):
        raise BadHeaderValue('header value name={name} value={val} '
                             'contained an illegal character'
                             .format(name=name or '?', val=repr(val)))


def escape_header_attr(val):
    # Escape quotes and slash like the hawk reference code.
    val = val.replace('\\', '\\\\').replace('"', '\\"')
    val = val.replace('\n', '\\n')
    return val


def unescape_header_attr(val):
    # Un-do the hawk escaping.
    val = val.replace('\\n', '\n')
    val = val.replace('\\\\', '\\').replace('\\"', '"')
    return val


def prepare_header_val(val):
    val = escape_header_attr(val)
    validate_header_attr(val)
    return val


def normalize_header_attr(val):
    if not val:
        val = ''

    # Ensure we are working with Unicode for sanity. Note that non-ascii is not
    # allowed but that's caught later on.
    if isinstance(val, str):
        val = val.decode('utf8')
    val = val.encode('utf8')

    # Normalize like the hawk reference code.
    val = escape_header_attr(val)
    return val
