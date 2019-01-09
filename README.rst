======
Mohawk
======
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

Mohawk is an alternate Python implementation of the
`Hawk HTTP authorization scheme`_.

Hawk lets two parties securely communicate with each other using
messages signed by a shared key.
It is based on `HTTP MAC access authentication`_ (which
was based on parts of `OAuth 1.0`_).

The Mohawk API is a little different from that of the Node library
(i.e. `the living Hawk spec <https://github.com/hueniverse/hawk>`_).
It was redesigned to be more intuitive to developers, less prone to security problems, and more Pythonic.

Full documentation: https://mohawk.readthedocs.io/

.. _`Hawk HTTP authorization scheme`: https://github.com/hueniverse/hawk
.. _`HTTP MAC access authentication`: http://tools.ietf.org/html/draft-hammer-oauth-v2-mac-token-05
.. _`OAuth 1.0`: http://tools.ietf.org/html/rfc5849
