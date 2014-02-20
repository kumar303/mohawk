.. Mohawk documentation master file, created by
   sphinx-quickstart on Tue Feb 18 14:47:38 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

======
Mohawk
======

Mohawk is an alternate Python implementation of the
`Hawk HTTP authorization scheme`_.

Hawk lets two parties securely communicate with each other using
messages signed by a shared key.
It is based on `HTTP MAC access authentication`_ (which
was based on parts of `OAuth 1.0`_).

The Mohawk API is a little different from that of the Node library.
It was redesigned to be more intuitive to developers, less prone to security
problems, and more Pythonic.

.. _`Hawk HTTP authorization scheme`: https://github.com/hueniverse/hawk
.. _`HTTP MAC access authentication`: http://tools.ietf.org/html/draft-hammer-oauth-v2-mac-token-05
.. _`OAuth 1.0`: http://tools.ietf.org/html/rfc5849

Installation
============

Using `pip`_ and Python >= 2.7::

    pip install mohawk


If you want to install from source, visit https://github.com/kumar303/mohawk

.. _pip: http://pip.readthedocs.org/

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

TODO
====

* Implement bewit. **The bewit URI scheme is not implemented at this time.**
* Support SNTP synchronization for local server time.
* Support auto-retrying a :class:`mohawk.Sender` request with an offset if
  there is timestamp skew.

Changelog
---------

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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

