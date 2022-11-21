Codecs - Encoders and Decoders
==============================

Ethereum Contract ABIv2
-----------------------

For a definitive reference to the Ethereum contract ABIv2 specification, `visit the solidity documentation <https://docs.soliditylang.org/en/develop/abi-spec.html>`_.

.. automodule:: eth.codecs.abi
   :members:

Hypothesis Strategies
^^^^^^^^^^^^^^^^^^^^^

.. py:module:: eth.codecs.abi.strategies

.. py:data:: schema
   :type: hypothesis.strategies.SearchStrategy[str]

   Generates a valid ABIv2 type schema (type string).

   .. rubric:: Example

   .. code-block:: python

      >>> from eth.codecs.abi.strategies import schema as st_schema
      >>> st_schema.example()
      '(bytes18,uint168,bool,int240[])[3]'

.. py:function:: value(schema: str) -> hypothesis.strategies.SearchStrategy[Any]

   Generate a valid ABIv2 encodable value for a given type schema.

   :param str schema: A valid ABIv2 type string.
   :returns: An encodable value for the given schema.

   .. rubric:: Example

   .. code-block:: python

      >>> from eth.codecs.abi.strategies import value as st_value
      >>> st_value("(uint256,uint8,address[2])").example()
      (163, 227, ['0x67BeeB3dCFa0498B362315501258878eCbE5DeC9', '0x67BeeB3dCFa0498B362315501258878eCbE5DeC9'])

.. py:function:: schema_and_value(st_type: hypothesis.strategies.SearchStrategy | None) -> hypothesis.strategies.SearchStrategy[tuple[str, Any]]

   Generate a valid ABIv2 type schema and an encodable value for it.

   If the ``st_type`` parameter is supplied, schemas will be generated using the supplied search strategy.

   :param hypothesis.strategies.SearchStrategy st_type: A search strategy which generates :py:class:`eth.codecs.abi.nodes.ABITypeNode`
   :returns: A tuple containing a valid ABIv2 type schema and a valid encodable value.

   .. rubric:: Example

   .. code-block:: python

      >>> from eth.codecs.abi.strategies import schema_and_value as st_schema_and_value
      >>> st_schema_and_value().example()
      ('bool[2][]', [[False, True], [False, False], [False, False], [False, True], [True, False], [True, False]])
      >>> from eth.codecs.abi.strategies.nodes import Fixed as st_fixed
      >>> st_schema_and_value(st_fixed).example()
      ('fixed96x75', Decimal('-1.6503499995656503835410387807E-47'))

Command Line Interface
^^^^^^^^^^^^^^^^^^^^^^

The :py:mod:`eth.codecs.abi` package provides a simple command line interface for encoding and decoding values.

.. code-block:: bash

   $ python -m eth.codecs.abi encode '(uint256[2])' '[[3, 3]]'
   0x00000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000003
   $ python -m eth.codecs.abi encode string '"Hello World!"'
   0x000000000000000000000000000000000000000000000000000000000000000c48656c6c6f20576f726c6421
   $ python -m eth.codecs.abi decode bytes4 '0x1232345800000000000000000000000000000000000000000000000000000000'
   0x12323458

*The value to be encoded/decoded should be quoted as a string to prevent any argument parsing errors.*

Utilities
---------

Additional encoder and decoder functions.

.. automodule:: eth.codecs.utils
   :members:
