# This file is part of the eth-stdlib library.
# Copyright (C) 2022 Edward Amor
#
# The eth-stdlib library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# The eth-stdlib library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import decimal
from collections import deque
from operator import lshift, rshift
from typing import Any

from eth.codecs.abi import nodes
from eth.codecs.abi.exceptions import DecodeError
from eth.codecs.utils import checksum_encode


class Decoder:
    """Ethereum contract ABIv2 decoder.

    Attributes:
        WORD_MASK: A bit mask equal to ``2**256 - 1``
    """

    WORD_MASK = 2**256 - 1

    @classmethod
    def decode(cls, node: nodes.ABITypeNode, value: bytes, **kwargs: Any) -> Any:
        """Decode a value.

        Parameters:
            node: The ABI type to decode the value as.
            value: The value to be decoded.

        Returns:
            The decoded value.

        Raises:
            DecodeError: If ``value`` can't be decoded.
            TypeError: If the ``node`` argument is not an instance of `nodes.ABITypeNode`,
                or if the ``value`` argument is not an instance of ``bytes``.
        """
        try:
            assert isinstance(node, nodes.ABITypeNode), (type(node).__qualname__, "node")
            assert isinstance(value, bytes), (type(value).__qualname__, "value")
        except AssertionError as e:
            typ, param = e.args[0]
            raise TypeError(f"Received invalid type {typ!r} for parameter {param!r}")
        return node.accept(cls, value, **kwargs)

    @classmethod
    def validate_atom(cls, node: nodes.ABITypeNode, value: bytes, bits: int):
        """Validate an atomic type is within its type bounds.

        Parameters:
            node: An ABI type node.
            value: The bytes to validate.
            bits: The number of bits the value should occupy. Negative values shift
                left, and positive values shift right.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        # if bits is negative, shift to the left, otherwise shift to the right
        shift = lshift if bits < 0 else rshift
        try:
            assert len(value) == 32, "Value is not 32 bytes"
            sval = shift(int.from_bytes(value, "big"), abs(bits))
            # mask to fit only word-length
            assert (sval & cls.WORD_MASK) == 0, "Value outside type bounds"
        except AssertionError as e:
            raise DecodeError(str(node), value, e.args[0])

    @classmethod
    def visit_AddressNode(
        cls, node: nodes.AddressNode, value: bytes, checksum: bool = True, **kwargs: Any
    ) -> str:
        """Decode an address.

        Parameters:
            node: An address ABI type node.
            value: The bytes value to decode.
            checksum: Whether to checksum encode the result.

        Returns:
            The decoded address as a string.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        cls.validate_atom(node, value, 160)

        if checksum:
            return checksum_encode(value[-20:])
        return f"0x{value[-20:].hex()}"

    @classmethod
    def visit_ArrayNode(cls, node: nodes.ArrayNode, value: bytes, **kwargs: Any) -> list[Any]:
        """Decode an array.

        Parameters:
            node: An array ABI type node.
            value: The bytes value to decode.

        Returns:
            The decoded array as a list.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        length, val = node.length, value
        if node.length is None:
            # dynamic array is atleast 32 bytes
            if len(value) < 32:
                raise DecodeError(str(node), value, "Dynamic array value has invalid length")

            length, val = int.from_bytes(value[:32], "big"), value[32:]
            if length == 0:
                # length can only be 0 for dynamic arrays, in which case return an empty list
                return []
        elif len(value) < node.etype.width * length:
            # should be equal to the product of the subtype length with the array length
            raise DecodeError(str(node), value, "Static array value invalid length")

        # case 1: static array w/ static elements
        # case 2: dynamic array w/ static elements
        if not node.etype.is_dynamic:
            q, r = divmod(len(val), length)
            if r != 0:
                raise DecodeError(str(node), value, "Invalid array size")
            return [cls.decode(node.etype, val[i : i + q], **kwargs) for i in range(0, len(val), q)]

        # 3) static array, w/ dynamic elements
        # 4) dynamic array, w/ dynamic elements
        # element type is dynamic so their is a head + tail, the head contains pointers to the tail

        # generate the list of pointers (each pointer is 32 bytes)
        ptrs = [int.from_bytes(val[i : i + 32], "big") for i in range(0, length * 32, 32)]
        # generate the list of data, slice the data section from last pointer to end as last item
        data = [val[a:b] for a, b in zip(ptrs, ptrs[1:])] + [val[ptrs[-1] :]]
        # decode each element from the data section, the subtype will do validation
        return [cls.decode(node.etype, v, **kwargs) for v in data]

    @classmethod
    def visit_BooleanNode(cls, node: nodes.BooleanNode, value: bytes, **kwargs: Any) -> bool:
        """Decode a boolean.

        Parameters:
            node: A boolean ABI type node.
            value: The bytes value to decode.

        Returns:
            The decoded boolean.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        cls.validate_atom(node, value, 1)

        return bool.from_bytes(value, "big")

    @classmethod
    def visit_BytesNode(cls, node: nodes.BytesNode, value: bytes, **kwargs: Any) -> bytes:
        """Decode a byte array.

        Parameters:
            node: A bytes ABI type node.
            value: The bytes value to decode.

        Returns:
            The decoded byte array.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        if not node.is_dynamic:
            # fixed-width bytes are right padded with null bytes
            # therefore need to shift left
            cls.validate_atom(node, value, -node.size * 8)
            return value[: node.size]

        # dynamic values are encoded as size + bytes
        try:
            assert len(value) >= 32, "Invalid size for dynamic bytes"
            size = int.from_bytes(value[:32], "big")
            assert len(value[32 : 32 + size]) == size, "Data section is not the correct size"
        except AssertionError as e:
            raise DecodeError("bytes", value, e.args[0])

        return value[32 : 32 + size]

    @classmethod
    def visit_FixedNode(cls, node: nodes.FixedNode, value: bytes, **kwargs: Any) -> decimal.Decimal:
        """Decode a fixed point decimal.

        Parameters:
            node: A fixed point decimal ABI type node.
            value: The bytes value to decode.

        Returns:
            The decoded fixed point decimal.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        try:
            # decode as an integer
            ival = cls.decode(nodes.IntegerNode(node.bits, node.is_signed), value, **kwargs)
        except DecodeError as e:
            raise DecodeError(str(node), value, e.msg)

        with decimal.localcontext(decimal.Context(prec=80)):
            # return shifted value
            return decimal.Decimal(ival).scaleb(-node.precision)

    @staticmethod
    def visit_IntegerNode(node: nodes.IntegerNode, value: bytes, **kwargs: Any) -> int:
        """Decode an integer.

        Parameters:
            node: An integer ABI type node.
            value: The bytes value to decode.

        Returns:
            The decoded integer.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        try:
            assert len(value) == 32, "Value is not 32 bytes"

            # convert the bytes to an integer
            ival = int.from_bytes(value, "big", signed=node.is_signed)

            lo, hi = node.bounds
            assert lo <= ival <= hi, "Value is outside type bounds"
            return ival
        except AssertionError as e:
            raise DecodeError(str(node), value, e.args[0])

    @classmethod
    def visit_StringNode(cls, node: nodes.StringNode, value: bytes, **kwargs) -> str:
        """Decode a string.

        Uses 'surrogateescape' to handle decoding errors.
        See `error handlers <https://docs.python.org/3/library/codecs.html#error-handlers>`_

        Parameters:
            node: A string ABI type node.
            value: The bytes value to decode.

        Returns:
            The decoded string.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        try:
            return cls.decode(nodes.BytesNode(), value, **kwargs).decode(errors="surrogateescape")
        except DecodeError as e:
            raise DecodeError("string", value, e.msg) from e

    @classmethod
    def visit_TupleNode(cls, node: nodes.TupleNode, value: bytes, **kwargs) -> tuple:
        """Decode a tuple.

        Parameters:
            node: A tuple ABI type node.
            value: The bytes value to decode.

        Returns:
            The decoded tuple.

        Raises:
            DecodeError: If the value can't be decoded.
        """
        # value size should be >= the sum of the length of its components
        if len(value) < sum((elem.width for elem in node.ctypes)):
            raise DecodeError(str(node), value, "Value length is less than expected")

        pos, raw_head = 0, []
        for ctyp in node.ctypes:
            raw_head.append(value[pos : pos + ctyp.width])
            pos += ctyp.width

        if not node.is_dynamic:
            # no tail section
            return tuple(
                (cls.decode(ctyp, val, **kwargs) for ctyp, val in zip(node.ctypes, raw_head))
            )

        ctyps_and_vals = list(zip(node.ctypes, raw_head))

        # ptrs are in the head section, convert them to ints in a single list
        ptrs = [int.from_bytes(val, "big") for ctyp, val in ctyps_and_vals if ctyp.is_dynamic]
        # for each pointer copy the data from the dynamic section similar to array decoding
        data = deque([value[a:b] for a, b in zip(ptrs, ptrs[1:])] + [value[ptrs[-1] :]])
        # replace each ptr with its data - generator
        head = [data.popleft() if ctyp.is_dynamic else val for ctyp, val in ctyps_and_vals]

        # return the decoded elements
        return tuple([cls.decode(typ, val, **kwargs) for typ, val in zip(node.ctypes, head)])
