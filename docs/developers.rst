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

    virtualenv _virtualenv
    source _virtualenv/bin/activate
    pip install -r requirements/dev.txt
    python setup.py develop

.. note::

    Development commands such as building docs and publishing a release were
    last tested on Python 3.7.4 so you will probably need a version close to that.
    Use ``tox`` to develop features for older Python versions.

Build the docs
==============

In your virtualenv, you can build the docs like this::

    make -C docs/ html doctest
    open docs/_build/html/index.html

Publish a release
=================

Do this first to prepare for a release:

- make sure the changelog is up to date
- make sure you bumped the module version in ``setup.py``
- commit, tag (like ``git tag 0.3.1``), and push upstream
  (like ``git push --tags upstream``).

Run this from the repository root to publish a new release to `PyPI`_
as both a source distribution and wheel::

    rm -rf dist/*
    python setup.py sdist bdist_wheel
    twine upload dist/*


.. _virtualenv: https://pypi.python.org/pypi/virtualenv
.. _tox: https://tox.readthedocs.io/
.. _`PyPI`: https://pypi.python.org/pypi
