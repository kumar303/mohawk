.. _usage:

============
Using Mohawk
============

There are two parties involved in `Hawk`_ communication: a
:class:`sender <mohawk.Sender>` and a :class:`receiver <mohawk.Receiver>`.
They use a shared secret to sign and verify each other's messages.

**Sender**
    A client who wants to access a Hawk-protected resource.
    The client will sign their request and upon
    receiving a response will also verify the response signature.

**Receiver**
    A server that uses Hawk to protect its resources. The server will check
    the signature of an incoming request before accepting it. It also signs
    its response using the same shared secret.

What are some good use cases for Hawk? This library was built for the case of
securing API connections between two back-end servers. Hawk is a good
fit for this because you can keep the shared secret safe on each machine.
Hawk may not be a good fit for scenarios where you can't protect the shared
secret.

After getting familiar with usage, you may want to consult the :ref:`security`
section.

.. testsetup:: usage

    class Requests:
        def post(self, *a, **kw): pass
    requests = Requests()

    credentials = {'id': 'some-sender',
                   'key': 'some complicated SEKRET',
                   'algorithm': 'sha256'}
    allowed_senders = {}
    allowed_senders['some-sender'] = credentials

    class Memcache:
        def get(self, *a, **kw):
            return False
        def set(self, *a, **kw): pass
    memcache = Memcache()

Sending a request
=================

Let's say you want to make an HTTP request like this:

.. doctest:: usage

    >>> url = 'https://some-service.net/system'
    >>> method = 'POST'
    >>> content = 'one=1&two=2'
    >>> content_type = 'application/x-www-form-urlencoded'

Set up your Hawk request by creating a :class:`mohawk.Sender` object
with all the elements of the request that you need to sign:

.. doctest:: usage

    >>> from mohawk import Sender
    >>> sender = Sender({'id': 'some-sender',
    ...                  'key': 'some complicated SEKRET',
    ...                  'algorithm': 'sha256'},
    ...                 url,
    ...                 method,
    ...                 content=content,
    ...                 content_type=content_type)

This provides you with a Hawk ``Authorization`` header to send along
with your request:

.. doctest:: usage

    >>> sender.request_header
    u'Hawk mac="...", hash="...", id="some-sender", ts="...", nonce="..."'

Using the `requests`_ library just as an example, you would send your POST
like this:

 .. doctest:: usage

    >>> requests.post(url, data=content,
    ...               headers={'Authorization': sender.request_header,
    ...                        'Content-Type': content_type})

Notice how both the content and content-type values were signed by the Sender.
In the case of a GET request you'll probably need to sign empty strings like
``Sender(..., 'GET', content='', content_type='')``,
that is, if your request library doesn't
automatically set a content-type for GET requests.

If you only intend to work with :class:`mohawk.Sender`,
skip down to :ref:`verify-response`.

.. _`receiving-request`:

Receiving a request
===================

On the receiving end, such as a web server, you'll need to set up a
:class:`mohawk.Receiver` object to accept and respond to
:class:`mohawk.Sender` requests.

First, you need to give the receiver a callable that it can use to look
up sender credentials:

.. doctest:: usage

    >>> def lookup_credentials(sender_id):
    ...     if sender_id in allowed_senders:
    ...         # Return a credentials dictionary formatted like the sender example.
    ...         return allowed_senders[sender_id]
    ...     else:
    ...         raise LookupError('unknown sender')

An incoming request will probably arrive in an object like this,
depending on your web server framework:

.. doctest:: usage

    >>> request = {'headers': {'Authorization': sender.request_header,
    ...                        'Content-Type': content_type},
    ...            'url': url,
    ...            'method': method,
    ...            'content': content}

Create a :class:`mohawk.Receiver` using values from the incoming request:

.. doctest:: usage

    >>> from mohawk import Receiver
    >>> receiver = Receiver(lookup_credentials,
    ...                     request['headers']['Authorization'],
    ...                     request['url'],
    ...                     request['method'],
    ...                     content=request['content'],
    ...                     content_type=request['headers']['Content-Type'])

If this constructor does not raise any :ref:`exceptions` then the signature of
the request is correct and you can proceed.

Responding to a request
=======================

It's optional per the `Hawk`_ spec but a :class:`mohawk.Receiver`
should sign its response back to the client to prevent certain attacks.

The receiver starts by building a message it wants to respond with:

.. doctest:: usage

    >>> response_content = '{"msg": "Hello, dear friend"}'
    >>> response_content_type = 'application/json'
    >>> header = receiver.respond(content=response_content,
    ...                           content_type=response_content_type)

This provides you with a similar Hawk header to use in the response:

.. doctest:: usage

    >>> receiver.response_header
    u'Hawk mac="...", hash="...="'

Using your web server's framework, respond with a
``Server-Authorization`` header. For example:

.. doctest:: usage

    >>> response = {
    ...     'headers': {'Server-Authorization': receiver.response_header,
    ...                 'Content-Type': response_content_type},
    ...     'content': response_content
    ... }

.. _`verify-response`:

Verifying a response
====================

When the :class:`mohawk.Sender`
receives a response it should verify the signature to
make sure nothing has been tampered with:

.. doctest:: usage

    >>> sender.accept_response(response['headers']['Server-Authorization'],
    ...                        content=response['content'],
    ...                        content_type=response['headers']['Content-Type'])


If this method does not raise any :ref:`exceptions` then the signature of
the response is correct and you can proceed.

Allowing senders to adjust their clocks
=======================================

If a sender's clock is out of sync with the receiver, its message might
expire prematurely. In this case the receiver should respond with a header that
the sender can use to adjust its time.

When receiving a request you might get a :class:`mohawk.exc.TokenExpired`
exception. You can access the ``www_authenticate`` property on the
exception object to respond correctly like this:

.. doctest:: usage
    :hide:

    >>> exp_sender = Sender({'id': 'some-sender',
    ...                      'key': 'some complicated SEKRET',
    ...                      'algorithm': 'sha256'},
    ...                     url,
    ...                     method,
    ...                     content=content,
    ...                     content_type=content_type,
    ...                     _timestamp=1)
    >>> request['headers']['Authorization'] = exp_sender.request_header

.. doctest:: usage

    >>> from mohawk.exc import TokenExpired
    >>> try:
    ...     receiver = Receiver(lookup_credentials,
    ...                         request['headers']['Authorization'],
    ...                         request['url'],
    ...                         request['method'],
    ...                         content=request['content'],
    ...                         content_type=request['headers']['Content-Type'])
    ... except TokenExpired as expiry:
    ...     pass
    >>> expiry.www_authenticate
    'Hawk ts="...", tsm="...", error="token with UTC timestamp...has expired..."'
    >>> response['headers']['WWW-Authenticate'] = expiry.www_authenticate

.. doctest:: usage
    :hide:

    >>> request['headers']['Authorization'] = sender.request_header

A compliant client can look for this response header and parse the
``ts`` property (the server's "now" timestamp) and
the ``tsm`` property (a MAC calculation of ``ts``). It can then recalculate the
MAC using its own credentials and if the MACs both match it can trust that this
is the real server's timestamp. This allows the sender to retry the request
with an adjusted timestamp.

.. _nonce:

Using a nonce to prevent replay attacks
=======================================

A replay attack is when someone copies a Hawk authorized message and
re-sends the message without altering it.
Because the Hawk signature would still be valid, the receiver may
accept the message. This could have unintended side effects such as increasing
the quantity of an item just purchased if it were a commerce API that had an
``increment-item`` service.

Hawk protects against replay attacks in a couple ways. First, a receiver checks
the timestamp of the message which may result in a
:class:`mohawk.exc.TokenExpired` exception.
Second, every message includes a `cryptographic nonce`_
which is a unique
identifier. In combination with the timestamp, a receiver can use the nonce to
know if it has *already* received the request. If so,
the :class:`mohawk.exc.AlreadyProcessed` exception is raised.

By default, Mohawk doesn't know how to check nonce values; this is something
your application needs to do.

.. important::

    If you don't configure nonce checking, your application could be
    susceptible to replay attacks.

Make a callable that returns True if a nonce plus its timestamp has been
seen already. Here is an example using something like memcache:

.. doctest:: usage

    >>> def seen_nonce(nonce, timestamp):
    ...     key = '{nonce}:{ts}'.format(nonce=nonce, ts=timestamp)
    ...     if memcache.get(key):
    ...         # We have already processed this nonce + timestamp.
    ...         return True
    ...     else:
    ...         # Save this nonce + timestamp for later.
    ...         memcache.set(key, True)
    ...         return False

Because messages will expire after a short time you don't need to store
nonces for much longer than that timeout. See :class:`mohawk.Receiver`
for the default timeout.

Pass your callable as a ``seen_nonce`` argument to :class:`mohawk.Receiver`:

.. doctest:: usage

    >>> receiver = Receiver(lookup_credentials,
    ...                     request['headers']['Authorization'],
    ...                     request['url'],
    ...                     request['method'],
    ...                     content=request['content'],
    ...                     content_type=request['headers']['Content-Type'],
    ...                     seen_nonce=seen_nonce)

If ``seen_nonce()`` returns True, :class:`mohawk.exc.AlreadyProcessed`
will be raised.

When a *sender* calls :meth:`mohawk.Sender.accept_response`, it will receive
a Hawk message but the nonce will be that of the original request.
In other words, the nonce received is the same nonce that the sender
generated and signed when initiating the request.
This generally means you don't have to worry about *response* replay attacks.
However, if you
expose your :meth:`mohawk.Sender.accept_response` call
somewhere publicly over HTTP then you
may need to protect against response replay attacks.
You can do so by constructing a :class:`mohawk.Sender` with
the same ``seen_nonce`` keyword:

.. doctest:: usage

    >>> sender = Sender({'id': 'some-sender',
    ...                  'key': 'some complicated SEKRET',
    ...                  'algorithm': 'sha256'},
    ...                 url,
    ...                 method,
    ...                 content=content,
    ...                 content_type=content_type,
    ...                 seen_nonce=seen_nonce)

.. _`cryptographic nonce`: http://en.wikipedia.org/wiki/Cryptographic_nonce

.. _skipping-content-checks:

Skipping content checks
=======================

In some cases you may not be able to sign request/response content. For example,
the content could be too large to fit in memory. If you run into this, Hawk
might not be the best fit for you but Hawk does allow you to skip content
checks if you wish.

.. important::

    By skipping content checks both the sender and receiver are
    susceptible to content tampering.

You can send a request without signing the content by passing this keyword
argument to a :class:`mohawk.Sender`:

.. doctest:: usage

    >>> sender = Sender(credentials, url, method, always_hash_content=False)

This says to skip hashing of the ``content`` and ``content_type`` values
if they are both ``None``.

Now you'll get an ``Authorization`` header without a ``hash`` attribute:

.. doctest:: usage

    >>> sender.request_header
    u'Hawk mac="...", id="some-sender", ts="...", nonce="..."'

The :class:`mohawk.Receiver` must also be constructed to
accept unsigned content with ``accept_untrusted_content=True``:

.. doctest:: usage

    >>> receiver = Receiver(lookup_credentials,
    ...                     sender.request_header,
    ...                     request['url'],
    ...                     request['method'],
    ...                     accept_untrusted_content=True)

Logging
=======

All internal `logging <http://docs.python.org/2/library/logging.html>`_
channels stem from ``mohawk``. For example, the ``mohawk.receiver``
channel will just contain receiver messages. These channels correspond
to the submodules within mohawk.

To debug :class:`mohawk.exc.MacMismatch` :ref:`exceptions`
and other authorization errors, set the ``mohawk`` channel to ``DEBUG``.

Going further
=============

Well, hey, that about summarizes the concepts and basic usage of Mohawk.
Check out the :ref:`API` for details.
Also make sure you are familiar with :ref:`security`.

.. _`Hawk`: https://github.com/hueniverse/hawk
.. _`requests`: http://docs.python-requests.org/
