.. eth-stdlib documentation master file, created by
   sphinx-quickstart on Thu Sep 29 22:46:49 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to eth-stdlib's documentation!
======================================

The Ethereum Standard Library is a collection of libraries for developers building on the EVM.
The intention is to have a single repository of data structures and utilities which is easy to grok and just as
easy to install as a dependency.

Installation
------------

``eth-stdlib`` is available on `PyPi <https://pypi.org/project/eth-stdlib/>`_ for download, and on `github <https://github.com/skellet0r/eth-stdlib>`_ for source installs.

Installing via pip:

.. code-block:: bash

   $ pip install eth-stdlib

Installing via poetry:

.. code-block:: bash

   $ poetry add eth-stdlib

Optionally, the ``hypothesis`` extras can be installed to gain access to built-in testing strategies:

.. code-block:: bash

   $ pip install eth-stdlib[hypothesis]

Usage
-----

After installing locally, the ``eth`` namespace will be available to import in Python applications and scripts.

.. code-block:: python

   >>> from eth.codecs import abi
   >>> abi.encode("uint256", 42)
   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00*'
   >>> abi.decode("uint8", b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10')
   16
   >>> from eth.hash import keccak256
   >>> keccak256(b"Hello World!").hex()
   '3ea2f1d0abf3fc66cf29eebb70cbd4e7fe762ef8a09bcc06c8edf641230afec0'

Indices and tables
==================

.. toctree::
   :maxdepth: 2

   codecs
   hash

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
