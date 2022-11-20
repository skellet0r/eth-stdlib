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

.. py:function:: value(schema: str) -> Any

   Generate a valid ABIv2 encodable value for a given type schema.

   :param str schema: A valid ABIv2 type string.
   :returns: An encodable value for the given schema.

   .. rubric:: Example

   .. code-block:: python

      >>> from eth.codecs.abi.strategies import value as st_value
      >>> st_value("(uint256,uint8,address[2])").example()
      (163, 227, ['0x67BeeB3dCFa0498B362315501258878eCbE5DeC9', '0x67BeeB3dCFa0498B362315501258878eCbE5DeC9'])

Utilities
---------

Additional encoder and decoder functions.

.. automodule:: eth.codecs.utils
   :members:
