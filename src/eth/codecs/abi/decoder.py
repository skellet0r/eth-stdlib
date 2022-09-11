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
from typing import Any

from eth.codecs.abi import nodes
from eth.codecs.abi.exceptions import DecodeError
from eth.codecs.abi.formatter import Formatter


class Decoder:
    @classmethod
    def decode(cls, node: nodes.Node, value: bytes) -> Any:
        try:
            assert isinstance(node, nodes.Node), ("node", type(node).__qualname__)
            assert isinstance(value, (bytes, bytearray)), ("value", type(value).__qualname__)
        except AssertionError as e:
            param, typ = e.args[0]
            raise TypeError(f"Received invalid type {typ!r} for parameter {param!r}")
        return node.accept(cls, value)

    @staticmethod
    def validate_atom(node: nodes.Node, value: bytes, bits: int):
        typestr = Formatter.format(node)
        try:
            assert len(value) == 32, "Value is not 32 bytes"
            assert int.from_bytes(value, "big") >> bits == 0, "Value outside type bounds"
        except AssertionError as e:
            raise DecodeError(typestr, value, e.args[0]) from e

    @classmethod
    def visit_Address(cls, node: nodes.Address, value: bytes) -> str:
        cls.validate_atom(node, value, 160)

        return f"0x{value[-20:].hex()}"

    @classmethod
    def visit_Array(cls, node: nodes.Array, value: bytes) -> list[Any]:
        # static arrays
        size, val = node.size, value
        if node.size == -1:
            # dynamic arrays
            assert len(value) >= 32  # validate the value is atleast 32 bytes
            size, val = int.from_bytes(value[:32], "big"), value[32:]

            if size == 0:  # size can only be 0 with dynamic arrays
                assert len(val) == 0  # validate the data section is emtpy
                return []

        # case 1: static array w/ static elements
        # case 2: dynamic array w/ static elements
        if not node.subtype.is_dynamic:
            q, r = divmod(len(val), size)
            assert r == 0, "Invalid array size"
            return [cls.decode(node.subtype, val[i : i + q]) for i in range(0, len(val), q)]

        # 3) static array, w/ dynamic elements
        # 4) dynamic array, w/ dynamic elements

        # slicing past bytes size returns empty bytes, validate we have a valid pointer section
        assert len(val) >= (width := size * 32)
        # generate the list of pointers (each pointer is 32 bytes)
        ptrs = [int.from_bytes(val[i : i + 32], "big") for i in range(0, width, 32)]
        # decode each element from the data section, the subtype will do validation
        # if the slice taken is less than expected
        return [cls.decode(node.subtype, val[a:b]) for a, b in zip(ptrs, [*ptrs[1:], width])]

    @classmethod
    def visit_Bool(cls, node: nodes.Bool, value: bytes) -> bool:
        cls.validate_atom(node, value, 1)

        return bool.from_bytes(value, "big")

    @classmethod
    def visit_Bytes(cls, node: nodes.Bytes, value: bytes) -> bytes:
        if not node.is_dynamic:
            # reverse the value since fixed-width bytes are right padded
            cls.validate_atom(node, value[::-1], node.size * 8)
            return value[: node.size]

        # dynamic values are encoded as size + bytes
        try:
            assert len(value) >= 32, "Invalid size for dynamic bytes"
            size = int.from_bytes(value[:32], "big")
            assert len(value[32 : 32 + size]) == size, "Data section is not the correct size"
        except AssertionError as e:
            raise DecodeError("bytes", value, e.args[0]) from e

        return value[32 : 32 + size]

    @classmethod
    def visit_Fixed(cls, node: nodes.Fixed, value: bytes) -> decimal.Decimal:
        try:
            # decode as an integer
            ival = cls.decode(nodes.Integer(node.size, node.is_signed), value)
        except DecodeError as e:
            raise DecodeError(Formatter.format(node), value, e.msg)

        with decimal.localcontext(decimal.Context(prec=128)):
            # return shifted value
            return decimal.Decimal(ival).scaleb(-node.precision)

    @staticmethod
    def visit_Integer(node: nodes.Integer, value: bytes) -> int:
        try:
            assert len(value) == 32, "Value is not 32 bytes"

            # calculate type bounds
            lo, hi = 0, 2**node.size - 1
            if node.is_signed:
                lo, hi = 2 ** (node.size - 1), 2 ** (node.size - 1) - 1

            # convert the bytes to an integer
            ival = int.from_bytes(value, "big", signed=node.is_signed)
            assert lo <= ival <= hi, "Value is outside type bounds"
            return ival
        except AssertionError as e:
            raise DecodeError(Formatter.format(node), value, e.args[0])

    @classmethod
    def visit_String(cls, node: nodes.String, value: bytes) -> str:
        try:
            return cls.decode(nodes.Bytes(-1), value).decode()
        except DecodeError as e:
            raise DecodeError("string", value, e.msg) from e

    @staticmethod
    def visit_Tuple(node: nodes.Tuple, value: bytes) -> list[Any]:
        pass
