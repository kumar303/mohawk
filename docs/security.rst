.. _security:

=======================
Security Considerations
=======================

`Hawk`_ HTTP authorization uses a message authentication code (MAC)
algorithm to provide partial cryptographic verification of HTTP
requests/responses.

.. important::

    Take a look at Hawk's own `security considerations`_.

Here are some additional security considerations:

* ``mohawk`` is intended to be used as a low-level library.
  You should *never* expose its :ref:`exceptions` publicly, say,
  in an HTTP response, as they may provide hints to an attacker.
* Using a shared secret for signatures means that if the secret leaks out
  then messages can be signed all day long.
  Make sure secrets are stored somewhere safe and never
  transmitted over an insecure channel.
  For example, putting a shared secret in memory on a web browser page
  may or may not be secure enough.
* What does *partial verification* mean?
  While all major request/response artifacts are signed
  (URL, protocol, method, content),
  *only* the ``content-type`` header is signed. You'll want to make sure your
  sender and receiver aren't susceptible to header poisoning in case an attacker
  finds a way to replay a valid Hawk request with additional headers.
  For example, if an attacker can find a way to replay a request and add
  the header ``x-token: hijacked-token`` then the request might still be
  valid because this random header is not part of the signature.
* Consider :ref:`nonce`.
* Hawk lets you verify that you're talking to the person you think you are.
  In a lot of ways, this is more trustworthy than SSL/TLS but to guard
  against your own `stupidity`_ as well as prevent general eavesdropping,
  you should probably use both HTTPS and Hawk.
* The `Hawk`_ spec says that signing request/response content is *optional*
  but just for extra paranoia, Mohawk
  raises an exception if you skip content checks unintentionally.
  Read :ref:`skipping-content-checks` for how to intentionally make it
  optional. This does not apply to :ref:`empty requests <empty-requests>`.

.. _`Hawk`: https://github.com/hueniverse/hawk
.. _stupidity: http://benlog.com/2010/09/07/defending-against-your-own-stupidity/
.. _`security considerations`: https://github.com/hueniverse/hawk#security-considerations
