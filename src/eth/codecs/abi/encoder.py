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
from itertools import accumulate
from typing import Any

from eth.codecs.abi import nodes
from eth.codecs.abi.exceptions import EncodeError


class Encoder:
    """Ethereum contract ABIv2 encoder."""

    @classmethod
    def encode(cls, node: nodes.ABITypeNode, value: Any) -> bytes:
        """Encode a value according to an ABI type.

        Parameters:
            node: The ABI type node to encode the value as.
            value: The value to be encoded.

        Returns:
            The encoded value.

        Raises:
            EncodeError: If value can't be encoded.
            TypeError: If the ``node`` argument is not an instance of `nodes.ABITypeNode`.
        """
        if not isinstance(node, nodes.ABITypeNode):
            raise TypeError(f"Invalid argument type for `node`: {type(node).__qualname__!r}")

        return node.accept(cls, value)

    @classmethod
    def visit_AddressNode(cls, node: nodes.AddressNode, value: str) -> bytes:
        """Encode an address.

        Address values are encoded the same as the uint160 ABI type. There is no
        verification of whether the value is checksummed or not.

        Parameters:
            node: The address ABI node type.
            value: The address value to encode.

        Returns:
            An ABIv2 encoded address.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        try:
            bval = bytes.fromhex(value.removeprefix("0x"))
            assert len(bval) == 20
            return bval.rjust(32, b"\x00")
        except (AttributeError, TypeError):
            # TypeError - if `value` is not a `str` instance (if value == bytes)
            raise EncodeError("address", value, "Value is not an instance of type 'str'")
        except ValueError:
            # ValueError - if value contains non-hexadecimal characters (e.g "-0x...", "0xSJ32...")
            raise EncodeError("address", value, "Value contains non-hexadecimal number(s)")
        except AssertionError:
            # AssertionError - does not fit in the type bounds (not 20 bytes)
            raise EncodeError("address", value, "Value is not 20 bytes")

    @classmethod
    def visit_ArrayNode(cls, node: nodes.ArrayNode, value: list | tuple) -> bytes:
        """Encode an array.

        There are 4 possible cases when encoding an array:

            #. static array with static elements
            #. dynamic array with static elements
            #. static array with dynamic elements
            #. dynamic array with dynamic elements

        Arrays with dynamic length are encoded with the number of elements prepended to the
        static data section. Arrays with dynamic elements have pointers in the static data
        section, pointing to the start of the encoded element in the dynamic data section.

        See `ABIv2 Spec <https://docs.soliditylang.org/en/develop/abi-spec.html>`_.

        Parameters:
            node: The array ABI node type.
            value: The array value to encode.

        Returns:
            An ABIv2 encoded array.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        try:
            assert isinstance(
                value, (list, tuple)
            ), "Value is not an instance of type 'list' or 'tuple'"
            if node.length is not None:
                assert len(value) == node.length, f"Expected value of size {node.length}"
        except AssertionError as e:
            raise EncodeError(str(node), value, e.args[0])

        tail = [cls.encode(node.etype, val) for val in value]
        if not node.is_dynamic:
            # case 1: return the concatenation of the encoded elements
            return b"".join(tail)
        elif node.length is None and not node.etype.is_dynamic:
            # case 2: return the encoded size of the array concatenated with the encoded elements
            # of the array concatenated
            return len(value).to_bytes(32, "big") + b"".join(tail)

        # calculate the width of the static-head section, each element is a pointer (32 bytes)
        width = 32 * len(value)
        # calculate each encoded element's offset from the start of the dynamic-tail section
        # offset[0] = 0, offset[1] = len(elem[0]), offset[2] = offset[1] + len(elem[1]), ...
        # the last elements's offset is the sum of all previous elements' length
        offsets = [0, *accumulate(map(len, tail))][:-1]
        # calculate the pointers, which are just the width + offset
        head = [(width + offset).to_bytes(32, "big") for offset in offsets]

        if node.length is not None:
            # case 3: return the concatenation of the static-head and dynamic-tail, each element in
            # the head is a pointer to it's element in the tail
            return b"".join(head + tail)

        # case 4: similar to case 4 return the concatenation of the static-head and dynamic-tail,
        # except also prepend the encoded size of the array. Each element is again a pointer to
        # it's element in the tail
        return len(value).to_bytes(32, "big") + b"".join(head + tail)

    @classmethod
    def visit_BooleanNode(cls, node: nodes.BooleanNode, value: bool) -> bytes:
        """Encode a boolean.

        Booleans are encoded the same as a uint256, but with the type bounds being [0, 1].

        Parameters:
            node: The boolean ABI node type.
            value: The boolean value to encode.

        Returns:
            An ABIv2 encoded boolean.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        if not isinstance(value, bool):
            raise EncodeError("bool", value, "Value is not an instance of type 'bool'")
        return cls.encode(nodes.IntegerNode(1), value)

    @staticmethod
    def visit_BytesNode(node: nodes.BytesNode, value: bytes) -> bytes:
        """Encode a byte array.

        Fixed width byte arrays are encoded by padding the left, up to the width, with null
        bytes. Whereas a dynamic byte array is encoded by prepending the value with the encoded
        length of the value.

        Parameters:
            node: The bytes ABI node type.
            value: The bytes value to encode.

        Returns:
            An ABIv2 encoded byte array.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        try:
            assert isinstance(value, bytes), "Value is not an instance of type 'bytes'"
            length = len(value)
            if not node.is_dynamic:
                assert length <= node.size, f"Value is not {node.size} bytes in length"
        except AssertionError as e:
            raise EncodeError(str(node), value, e.args[0])

        # dyanmic
        if node.is_dynamic:
            # no padding, null bytes cost extra
            return length.to_bytes(32, "big") + value

        # static - requires padding to occupy a full word length
        return value.rjust(node.size, b"\x00").ljust(32, b"\x00")

    @staticmethod
    def visit_FixedNode(node: nodes.FixedNode, value: decimal.Decimal) -> bytes:
        """Encode a fixed point decimal.

        Parameters:
            node: The fixed point decimal ABI node type.
            value: The fixed point decimal value to encode.

        Returns:
            An ABIv2 encoded fixed point decimal.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        try:
            assert isinstance(
                value, decimal.Decimal
            ), "Value is not an instance of type 'decimal.Decimal'"
            lo, hi = node.bounds
            assert lo <= value <= hi, "Value outside type bounds"

            with decimal.localcontext(decimal.Context(prec=128)) as ctx:
                # using to_integral_exact will signal Inexact if non-zero digits were rounded off
                # https://docs.python.org/3/library/decimal.html#decimal.Decimal.to_integral_exact
                scaled_value = int(value.scaleb(node.precision).to_integral_exact())
                assert not ctx.flags[decimal.Inexact], "Precision of value is greater than allowed"
        except AssertionError as e:
            raise EncodeError(str(node), value, e.args[0])

        return scaled_value.to_bytes(32, "big", signed=node.is_signed)

    @staticmethod
    def visit_IntegerNode(node: nodes.IntegerNode, value: int) -> bytes:
        """Encode an integer.

        Parameters:
            node: The integer ABI node type.
            value: The integer value to encode.

        Returns:
            An ABIv2 encoded integer.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        try:
            assert isinstance(value, int), "Value not an instance of type 'int'"
            lo, hi = node.bounds
            assert lo <= value <= hi, "Value outside type bounds"
        except AssertionError as e:
            raise EncodeError(str(node), value, e.args[0])

        return value.to_bytes(32, "big", signed=node.is_signed)

    @classmethod
    def visit_StringNode(cls, node: nodes.StringNode, value: str) -> bytes:
        """Encode a string.

        Strings are encoded exactly the same as dynamic byte arrays.

        Parameters:
            node: The string ABI node type.
            value: The string value to encode.

        Returns:
            An ABIv2 encoded string.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        try:
            return cls.encode(nodes.BytesNode(), value.encode())
        except (AttributeError, EncodeError):
            # AttributeError - if value does not have encode method
            # EncodeError - if value.encode() does not return a bytes instance
            raise EncodeError("string", value, "Value is not an instance of type 'str'")

    @classmethod
    def visit_TupleNode(cls, node: nodes.TupleNode, value: list | tuple) -> bytes:
        """Encode a tuple.

        There are 2 possible cases when encoding a tuple:

            #. All components are static
            #. One or more components are dynamic

        Similar to arrays, dynamic data is encoded and placed in the dynamic data section,
        and a pointer is placed in the static data section.

        Parameters:
            node: The tuple ABI node type.
            value: The tuple value to encode.

        Returns:
            An ABIv2 encoded tuple.

        Raises:
            EncodeError: If the value can't be encoded.
        """
        try:
            # validate value is a list or tuple of appropriate size
            assert isinstance(
                value, (list, tuple)
            ), "Value is not an instance of type 'list' or 'tuple'"
            assert len(node.ctypes) == len(value), f"Expected value of size {len(node.ctypes)}"
        except AssertionError as e:
            raise EncodeError(str(node), value, e.args[0])

        if not node.is_dynamic:
            # case 1: return the concatentation of each encoded element
            return b"".join((cls.encode(ctyp, val) for ctyp, val, in zip(node.ctypes, value)))

        # case 2: similar to a dynamic array, there is a static-head w/ pointers to the
        # dynamic-tail section for dynamic elements
        raw_head, tail = [], []
        for ctyp, val in zip(node.ctypes, value):
            output = cls.encode(ctyp, val)
            # if the element is dynamic append None to the head section (to be later replaced
            # with a pointer), and the encoded element in the tail section
            # if the element is static, append the encoded element in the head section,
            # and an empty (0-width) bytes value to the tail
            raw_head.append(None if ctyp.is_dynamic else output)
            tail.append(output if ctyp.is_dynamic else b"")

        # calculate the width of the static-head section
        # since elements in the head section can be different types, they
        # can potentially occupy more than 32 bytes (such as arrays, or tuples)
        # so we take the sum of the length of each element (replacing None values
        # with 32, the size of a pointer)
        width = sum((32 if val is None else len(val) for val in raw_head))
        # calculate each dynamic element's offset from the start of the dynamic-tail
        # used for calculating pointers (similar to array encoding)
        offsets = [0, *accumulate(map(len, tail))][:-1]

        # recalculate the head section with pointers this time
        head = []
        for val, offset in zip(raw_head, offsets):
            ptr = (width + offset).to_bytes(32, "big")
            head.append(ptr if val is None else val)

        return b"".join(head + tail)
