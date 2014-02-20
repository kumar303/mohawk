==========
Developers
==========

Grab the source from Github: https://github.com/kumar303/mohawk

Run the tests
=============

You can run the full test suite with the `tox`_ command::

    tox

To just run Python 2.7 unit tests type::

    tox -e py27

To just run doctests type::

    tox -e docs

Set up an environment
=====================

Using a `virtualenv`_ you can set yourself up for development like this::

    pip install -r requirements/dev.txt
    python setup.py develop

Build the docs
==============

Tox will leave documentation artifacts in ``.tox/docs/tmp/html/index.html``
but you can also build them manually like this::

    make -C docs/ html doctest
    open docs/_build/html/index.html


.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _tox: http://tox.readthedocs.org/
