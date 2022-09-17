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
from eth.codecs.abi.formatter import Formatter


class Encoder:
    """Ethereum ABI Encoder."""

    @classmethod
    def encode(cls, node: nodes.Node, value: Any) -> bytes:
        """Encode a value according to an ABI type.

        Parameters:
            node: The ABI type to encode the value as.
            value: The value to be encoded.

        Returns:
            The encoded value.

        Raises:
            EncodeError: If value, or sub-sequence thereof, can't be encoded.
            TypeError: If node argument is not an instance of `nodes.Node`.
        """
        if not isinstance(node, nodes.Node):
            raise TypeError(f"Invalid argument type for node: {type(node).__qualname__!r}")

        return node.accept(cls, value)

    @staticmethod
    def visit_Address(node: nodes.Address, value: str) -> bytes:
        try:
            bval = bytes.fromhex(value.removeprefix("0x"))
            assert len(bval) == 20
            return bval.rjust(32, b"\x00")
        except (AttributeError, TypeError) as e:
            # AttributeError - if `value` does not have `removeprefix` method (only bytes | str)
            # TypeError - if `value` is not a `str` instance (if value == bytes)
            raise EncodeError("address", value, "Value is not an instance of type 'str'") from e
        except ValueError as e:
            # ValueError - if value contains non-hexadecimal characters (e.g "-0x...", "0xSJ32...")
            raise EncodeError("address", value, "Value contains non-hexadecimal number(s)") from e
        except AssertionError as e:
            # AssertionError - if length of the bytes value is not 20
            raise EncodeError("address", value, "Value is not 20 bytes") from e

    @classmethod
    def visit_Array(cls, node: nodes.Array, value: list | tuple) -> bytes:
        try:
            # validate value is a list or tuple of appropriate size
            assert isinstance(value, (list, tuple)), "Value is not a list | tuple type"
            if node.size != -1:
                assert len(value) == node.size, f"Expected value of size {node.size}"
        except AssertionError as e:
            raise EncodeError(Formatter.format(node), value, e.args[0]) from e

        # there are 4 possible cases when encoding an array
        # 1) static array, w/ static elements
        # 2) dynamic array, w/ static elements - ptr
        # 3) static array, w/ dynamic elements - ptr
        # 4) dynamic array, w/ dynamic elements - ptr

        tail = [cls.encode(node.subtype, val) for val in value]
        if not node.is_dynamic:
            # case 1: return the concatenation of the encoded elements
            return b"".join(tail)
        elif node.size == -1 and not node.subtype.is_dynamic:
            # case 2: return the encoded size of the array concatenated with the encoded elemnts
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

        if node.size != -1:
            # case 3: return the concatenation of the static-head and dynamic-tail, each element in
            # the head is a pointer to it's element in the tail
            return b"".join(head + tail)

        # case 4: similar to case 4 return the concatenation of the static-head and dynamic-tail,
        # except also prepend the encoded size of the array. Each element is again a pointer to
        # it's element in the tail
        return len(value).to_bytes(32, "big") + b"".join(head + tail)

    @staticmethod
    def visit_Bool(node: nodes.Bool, value: bool) -> bytes:
        try:
            assert isinstance(value, bool), "Value is not an instance of type 'bool'"
            return value.to_bytes(32, "big")
        except AssertionError as e:
            raise EncodeError("bool", value, e.args[0]) from e

    @staticmethod
    def visit_Bytes(node: nodes.Bytes, value: bytes) -> bytes:
        try:
            assert isinstance(value, (bytes, bytearray)), "Value is not an instance of type 'bytes'"
            length = len(value)
            if not node.is_dynamic:
                assert length <= node.size, f"Value is not {node.size} bytes"
        except AssertionError as e:
            raise EncodeError(Formatter.format(node), value, e.args[0]) from e

        # dyanmic
        if node.is_dynamic:
            if length % 32 != 0:
                # pad end with null bytes up to nearest word
                width = length + 32 - (length % 32)
                value = value.ljust(width, b"\x00")
            return length.to_bytes(32, "big") + value

        # static
        return value.rjust(node.size, b"\x00").ljust(32, b"\x00")

    @staticmethod
    def visit_Fixed(node: nodes.Fixed, value: decimal.Decimal) -> bytes:
        typestr = Formatter.format(node)
        if not isinstance(value, decimal.Decimal):
            raise EncodeError(typestr, value, "Value is not an instance of type 'decimal.Decimal'")

        # calculate the integer type bounds
        ilo, ihi = 0, 2**node.size - 1
        if node.is_signed:
            subtrahend = 2 ** (node.size - 1)
            ilo, ihi = ilo - subtrahend, ihi - subtrahend

        with decimal.localcontext(decimal.Context(prec=128)) as ctx:
            # finalize type bound calculation by dividing by scalar 10**-precision
            lo, hi = [decimal.Decimal(v).scaleb(-node.precision) for v in [ilo, ihi]]

            try:
                assert lo <= value <= hi, "Value outside type bounds"
                scaled_value = int(value.scaleb(node.precision).to_integral_exact())
                # using to_integral_exact will signal Inexact if non-zero digits were rounded off
                # https://docs.python.org/3/library/decimal.html#decimal.Decimal.to_integral_exact
                assert not ctx.flags[decimal.Inexact], "Precision of value is greater than allowed"
            except AssertionError as e:
                raise EncodeError(typestr, value, e.args[0]) from e

        return scaled_value.to_bytes(32, "big", signed=node.is_signed)

    @staticmethod
    def visit_Integer(node: nodes.Integer, value: int) -> bytes:
        # calculate type bounds
        lo, hi = 0, 2**node.size - 1
        if node.is_signed:
            lo, hi = lo - 2 ** (node.size - 1), hi - 2 ** (node.size - 1)

        try:
            assert isinstance(value, int), "Value not an instance of type 'int'"
            # validate value fits in type and is of type int
            assert lo <= value <= hi, "Value outside type bounds"
        except AssertionError as e:
            # value can be a float, in which case it's not valid
            raise EncodeError(Formatter.format(node), value, e.args[0]) from e

        return value.to_bytes(32, "big", signed=node.is_signed)

    @classmethod
    def visit_String(cls, node: nodes.String, value: str) -> bytes:
        try:
            return cls.encode(nodes.Bytes(-1), value.encode())
        except (AttributeError, EncodeError) as e:
            # AttributeError - if value does not have encode method
            # EncodeError - if value.encode() does not return a bytes | bytearray instance
            raise EncodeError("string", value, "Value is not an instance of type 'str'") from e

    @classmethod
    def visit_Tuple(cls, node: nodes.Tuple, value: list | tuple) -> bytes:
        try:
            # validate value is a list or tuple of appropriate size
            assert isinstance(value, (list, tuple)), "Value is not a list | tuple type"
            assert len(node.components) == len(
                value
            ), f"Expected value of size {len(node.components)}"
        except AssertionError as e:
            raise EncodeError(Formatter.format(node), value, e.args[0]) from e

        # there are 2 possible cases when encoding a tuple
        # 1) all components are static
        # 2) at least 1 component is dynamic

        if not node.is_dynamic:
            # case 1: return the concatentation of each encoded element
            return b"".join([cls.encode(typ, val) for typ, val, in zip(node.components, value)])

        # case 2: similar to a dynamic array, there is a static-head w/ pointers to the
        # dynamic-tail section for dynamic elements
        raw_head, tail = [], []
        for typ, val in zip(node.components, value):
            output = cls.encode(typ, val)
            # if the element is dynamic append None to the head section (to be later replaced
            # with a pointer), and the encoded element in the tail section
            # if the element is static, append the encoded element in the head section,
            # and an empty (0-width) bytes value to the tail
            raw_head.append(None if typ.is_dynamic else output)
            tail.append(output if typ.is_dynamic else b"")

        # calculate the width of the static-head section
        # since elements in the head section can be different types, they
        # can potentially occupy more than 32 bytes (such as arrays, or tuples)
        # so we take the sum of the length of each element (replacing None values
        # with 32, the size of a pointer)
        width = sum([32 if val is None else len(val) for val in raw_head])
        # calculate each dynamic element's offset from the start of the dynamic-tail
        # used for calculating pointers (similar to array encoding)
        offsets = [0, *accumulate(map(len, tail))][:-1]

        # recalculate the head section with pointers this time
        head = []
        for val, offset in zip(raw_head, offsets):
            ptr = (width + offset).to_bytes(32, "big")
            head.append(ptr if val is None else val)

        return b"".join(head + tail)
