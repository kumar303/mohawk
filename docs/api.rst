.. _api:

===
API
===

This is a detailed look at the Mohawk API.
For general usage patterns see :ref:`usage`.

Sender
======

.. autoclass:: mohawk.Sender
    :members: request_header, accept_response

Receiver
========

.. autoclass:: mohawk.Receiver
    :members: response_header, respond

.. _exceptions:

Exceptions
==========

.. automodule:: mohawk.exc
    :members:

Base
====

.. autoclass:: mohawk.base.Resource

.. autodata:: mohawk.base.EmptyValue

    This represents an empty value but not ``None``.

    This is typically used as a placeholder of a default value
    so that internal code can differentiate it from ``None``.
