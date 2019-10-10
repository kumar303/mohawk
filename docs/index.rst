.. Mohawk documentation master file, created by
   sphinx-quickstart on Tue Feb 18 14:47:38 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

======
Mohawk
======

Mohawk is an alternate Python implementation of the
`Hawk HTTP authorization scheme`_.

.. image:: https://img.shields.io/pypi/v/mohawk.svg
    :target: https://pypi.python.org/pypi/mohawk
    :alt: Latest PyPI release

.. image:: https://img.shields.io/pypi/dm/mohawk.svg
    :target: https://pypi.python.org/pypi/mohawk
    :alt: PyPI monthly download stats

.. image:: https://travis-ci.org/kumar303/mohawk.svg?branch=master
    :target: https://travis-ci.org/kumar303/mohawk
    :alt: Travis master branch status

.. image:: https://readthedocs.org/projects/mohawk/badge/?version=latest
    :target: https://mohawk.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation status


Hawk lets two parties securely communicate with each other using
messages signed by a shared key.
It is based on `HTTP MAC access authentication`_ (which
was based on parts of `OAuth 1.0`_).

The Mohawk API is a little different from that of the Node library
(i.e. `the living Hawk spec <https://github.com/hueniverse/hawk>`_).
It was redesigned to be more intuitive to developers, less prone to security problems, and more Pythonic.

.. _`Hawk HTTP authorization scheme`: https://github.com/hueniverse/hawk
.. _`HTTP MAC access authentication`: http://tools.ietf.org/html/draft-hammer-oauth-v2-mac-token-05
.. _`OAuth 1.0`: http://tools.ietf.org/html/rfc5849

Installation
============

Requirements:

* Python 2.6+ or 3.4+
* `six`_

Using `pip`_::

    pip install mohawk


If you want to install from source, visit https://github.com/kumar303/mohawk

.. _pip: https://pip.readthedocs.io/

Bugs
====

You can submit bugs / patches on Github: https://github.com/kumar303/mohawk

.. important::

    If you think you found a security vulnerability please
    try emailing kumar.mcmillan@gmail.com before submitting a public issue.

Topics
======

.. toctree::
   :maxdepth: 2

   usage
   security
   api
   developers
   why

Framework integration
=====================

Mohawk is a low level library that focuses on Hawk communication.
The following higher-level libraries integrate Mohawk
into specific web frameworks:

* `Hawkrest`_: adds Hawk to `Django Rest Framework`_
* Did we miss one? Send a `pull request`_ so we can link to it.

.. _`Hawkrest`: https://hawkrest.readthedocs.io/
.. _`Django Rest Framework`: http://django-rest-framework.org/
.. _`pull request`: https://github.com/kumar303/mohawk

TODO
====

* Support NTP-like (but secure) synchronization for local server time.
  See `TLSdate <http://linux-audit.com/tlsdate-the-secure-alternative-for-ntpd-ntpdate-and-rdate/>`_.
* Support auto-retrying a :class:`mohawk.Sender` request with an offset if
  there is timestamp skew.

Changelog
---------

- **UNRELEASED**

  - Support passing file-like objects (supporting `.read(n)`) as the `content`
    parameter for Resources.
  - (Unreleased features should be listed here.)

- **1.0.0** (2019-01-09)

  - **Security related**: Bewit MACs were not compared in constant time and were thus
    possibly circumventable by an attacker.
  - **Breaking change**: Escape characters in header values (such as a back slash)
    are no longer allowed, potentially breaking clients that depended on this behavior.
    See https://github.com/kumar303/mohawk/issues/34
  - A sender is allowed to omit the content hash as long as their request has no
    content. The :class:`mohawk.Receiver` will skip the content hash check
    in this situation, regardless of the value of
    ``accept_untrusted_content``. See :ref:`empty-requests` for more details.
  - Introduced max limit of 4096 characters in the Authorization header
  - Changed default values of ``content`` and ``content_type`` arguments to
    :data:`mohawk.base.EmptyValue` in order to differentiate between
    misconfiguration and cases where these arguments are explicitly given as
    ``None`` (as with some web frameworks). See :ref:`skipping-content-checks`
    for more details.
  - Failing to pass ``content`` and ``content_type`` arguments to
    :class:`mohawk.Receiver` or :meth:`mohawk.Sender.accept_response`
    without specifying ``accept_untrusted_content=True`` will now raise
    :exc:`mohawk.exc.MissingContent` instead of :exc:`ValueError`.


- **0.3.4** (2017-01-07)

  - Fixed ``AttributeError`` exception
    (it now raises :class:`mohawk.exc.MissingAuthorization`) for cases
    when the client sends a None type authorization header.
    See `issue 23 <https://github.com/kumar303/mohawk/issues/23>`_.
  - Fixed Python 3.6 compatibility problem (a regex pattern was using
    the deprecated ``LOCALE`` flag).
    See `issue 32 <https://github.com/kumar303/mohawk/issues/32>`_.

- **0.3.3** (2016-07-12)

  - Fixed some cases where :class:`mohawk.exc.MacMismatch` was raised
    instead of :class:`mohawk.exc.MisComputedContentHash`.
    This follows the `Hawk HTTP authorization scheme`_ implementation
    more closely.
    See `issue 15 <https://github.com/kumar303/mohawk/issues/15>`_.
  - Published as a Python wheel

- **0.3.2.1** (2016-02-25)

  - Re-did the ``0.3.2`` release; the tag was missing some commits. D'oh.

- **0.3.2** (2016-02-24)

  - Improved Python 3 support.
  - Fixed bug in handling ``ext`` values that have more than one equal sign.
  - Configuration objects no longer need to be strictly dicts.

- **0.3.1** (2016-01-07)

  - Initial bewit support (undocumented).
    Complete support with documentation is still forthcoming.

- **0.3.0** (2015-06-22)

  - **Breaking change:** The ``seen_nonce()`` callback signature has changed.
    You must update your callback from ``seen_nonce(nonce, timestamp)``
    to ``seen_nonce(sender_id, nonce, timestamp)`` to avoid unnecessary
    collisions. See :ref:`nonce` for details.

- **0.2.2** (2015-01-05)

  - Receiver can now respond with a ``WWW-Authenticate`` header so that
    senders can adjust their timestamps. Thanks to jcwilson for the patch.

- **0.2.1** (2014-03-03)

  - Fixed Python 2 bug in how unicode was converted to bytes
    when calculating a payload hash.

- **0.2.0** (2014-03-03)

  - Added support for Python 3.3 or greater.
  - Added support for Python 2.6 (this was just a test suite fix).
  - Added `six`_ as dependency.
  - :attr:`mohawk.Sender.request_header` and
    :attr:`mohawk.Receiver.response_header` are now Unicode objects.
    They will never contain non-ascii characters though.

- **0.1.0** (2014-02-19)

  - Implemented optional content hashing per spec but in a less error prone way
  - Added complete documentation

- **0.0.4** (2014-02-11)

  - Bug fix: response processing now re-uses sender's nonce and timestamp
    per the Node Hawk lib
  - No longer assume content-type: text/plain if content type is not
    specificed

- **0.0.3** (2014-02-07)

  - Bug fix: Macs were made using URL safe base64 encoding which differs
    from the Node Hawk lib (it just uses regular base64)
  - exposed ``localtime_in_seconds`` on ``TokenExpired`` exception
    per Hawk spec
  - better localtime offset and skew handling

- **0.0.2** (2014-02-06)

  - Responding with a custom ext now works
  - Protected app and dlg according to spec when accepting responses

- **0.0.1** (2014-02-05)

  - initial release of partial implementation

.. _six: https://pypi.python.org/pypi/six

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
