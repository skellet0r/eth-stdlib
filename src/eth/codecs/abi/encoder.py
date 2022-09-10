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
    """Ethereum ABI encoder implementing the visitor pattern."""

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
        """
        return node.accept(cls, value)

    @staticmethod
    def visit_Address(_, value: str) -> bytes:
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

        # similar to tuples, arrays have a head and tail section
        tail = [cls.encode(node.subtype, val) for val in value]
        if not node.is_dynamic:
            # static w/ static subtype
            # a static array with non-dynamic elements
            # is just the concatenation of the encoded elements of the array
            # (b"" in the case of a dynamic array)
            return b"".join(tail)
        elif node.size == -1 and not node.subtype.is_dynamic:
            # dynamic w/ static subtype
            # size of array is dynamic but the elements are not dynamic
            # just return the size + the concatenation of the elements
            return len(value).to_bytes(32, "big") + b"".join(tail)

        # dynamic array with dynamic components
        # width of the head section
        head_width = 32 * len(value)
        # calculate offsets similar to tuple encoding
        offsets = [0, *accumulate(map(len, tail))][:-1]
        head = [(head_width + ofst).to_bytes(32, "big") for ofst in offsets]
        # for a static array we just return the encoded array, since the dynamic
        # elements will have pointers, and static elements will be in-place
        encoded = b"".join(head + tail)
        if node.size != -1:
            # static w/ dynamic subtype
            return encoded
        # dynamic w/ dynamic subtype
        # dynamic arrays we return the size of the array (number of elements)
        # concatenated with the encoded elements
        return len(value).to_bytes(32, "big") + encoded

    @staticmethod
    def visit_Bool(_, value: bool) -> bytes:
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

        # calculate the type bounds
        with decimal.localcontext(decimal.Context(prec=128)) as ctx:
            scalar = decimal.Decimal(10).scaleb(-node.precision)  # 10 ** -precision
            lo, hi = decimal.Decimal(0), decimal.Decimal(2**node.size - 1) * scalar
            if node.is_signed:
                lo, hi = (
                    decimal.Decimal(-(2 ** (node.size - 1))) * scalar,
                    decimal.Decimal(2 ** (node.size - 1) - 1) * scalar,
                )

            try:
                assert lo <= value <= hi, "Value outside type bounds"
                # take care of negative values here, they imply that node.is_signed is True
                scaled_value = (
                    int(value.scaleb(node.precision).to_integral_exact()) % 2**node.size
                )
                # using to_integral_exact will signal Inexact if non-zero digits were rounded off
                # https://docs.python.org/3/library/decimal.html#decimal.Decimal.to_integral_exact
                assert not ctx.flags[decimal.Inexact], "Precision of value is greater than allowed"
            except AssertionError as e:
                raise EncodeError(typestr, value, e.args[0]) from e

        if value < 0:  # implies node.is_signed is True
            width = (scaled_value.bit_length() + 7) // 8
            return scaled_value.to_bytes(width, "big").rjust(32, b"\xff")
        return scaled_value.to_bytes(32, "big")

    @staticmethod
    def visit_Integer(node: nodes.Integer, value: int) -> bytes:
        # calculate type bounds
        lo, hi = 0, 2**node.size - 1
        if node.is_signed:
            lo, hi = -(2 ** (node.size - 1)), 2 ** (node.size - 1) - 1

        try:
            # validate value fits in type and is of type int
            assert lo <= value <= hi, "Value outside type bounds"
            assert isinstance(value, int), "Value not an instance of type 'int'"
        except AssertionError as e:
            # value can be a float, in which case it's not valid
            raise EncodeError(Formatter.format(node), value, e.args[0]) from e
        except TypeError as e:
            raise EncodeError(
                Formatter.format(node), value, "Value not an instance of type 'int'"
            ) from e

        return value.to_bytes(32, "big", signed=node.is_signed)

    @classmethod
    def visit_String(cls, _, value: str) -> bytes:
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

        # since tuples are a composite type, they are composed of two sections
        # a head (static) and tail (dynamic). The head is where static data
        # belongs, and the tail is where dynamic data is placed. In the head
        # there will be a pointer to the dynamic section for any component
        # which is dynamic or is composed of dynamic subcomponents (and in the case of array/tuple)
        head, tail = [], []
        for component, val in zip(node.components, value):
            # if the component is dynamic we place the encoded output
            # in the tail section, and later we will fill the head
            # with the offset to the dynamic data
            output = cls.encode(component, val)
            head.append(None if component.is_dynamic else output)
            tail.append(output if component.is_dynamic else b"")

        # calculate the total width of the head
        # some items like statically sized arrays are placed in the head
        # section and take up more than 1 word
        head_width = sum([32 if val is None else len(val) for val in head])
        # calculate the offset from the start of the tail section for each
        # element in the tail section. i.e. the first element starts at
        # index 0, whereas the last element starts at index (sum(map(len, tail[:-1])))
        # when added with the head width, we have the exact offset position of a
        # dynamic piece of data in the tail section
        offsets = [0, *accumulate(map(len, tail))][:-1]
        # recompute the head, replacing None with the exact offset of the dynamic data
        new_head = [
            (head_width + ofst).to_bytes(32, "big") if val is None else val
            for val, ofst in zip(head, offsets)
        ]
        # concatenate the head and tail together
        return b"".join(new_head + tail)
