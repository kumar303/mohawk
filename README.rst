======
Mohawk
======

Mohawk is an alternate Python implementation of the
`Hawk HTTP authentication scheme`_.

If you don't see any documentation here it probably means the lib is unstable
and you shouldn't use it.

.. _`Hawk HTTP authentication scheme`: https://github.com/hueniverse/hawk

Why Mohawk?
-----------

* I started using `PyHawk`_ because it was written by Austin King and he's
  awesome.
* `PyHawk`_ is a direct port from Node but this did not seem to fit right
  with Python, especially in how Node's style is to attempt internal error
  recovery and Python's style is to raise exceptions that calling code
  can recover from.
* I was paranoid about how `PyHawk`_ (and maybe the Node lib too) makes it
  easy to ignore content hashing. If programmers accidentally
  disregard hash checks then that would be bad.
* I started patching `PyHawk`_ but became confused about the lifecycle of
  the request/response.
* PyHawk didn't have a lot of tests for edge cases (like content tampering) so
  it was hard to patch.
* I started on some Django middleware using PyHawk and found myself creating a
  lot of adapters for undocumented internal dictionary structures which felt
  wrong.
* The PyHawk/Node API relies on pre-generated header artifacts but this feels
  clunky to me. I wanted that to be an implementation detail.
* The required order in which you need to pre-generate artifacts is not
  implicitly enforced by the PyHawk/Node API which can lead to mistakes
  if programmers re-use objects across requests.
* I re-wrote the class/function interface into something that I thought made
  sense then I re-wrote it three more times until it started to
  actually make sense.
* I developed test first with a comprehensive suite focusing on the
  threat model that Hawk is designed to protect you from.
  This helped me arrive at an API that should help developers write secure
  applications by default.
* I re-used a lot of `PyHawk`_ code :)

.. _`PyHawk`: https://github.com/mozilla/PyHawk
