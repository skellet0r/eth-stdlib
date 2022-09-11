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
    def visit_Address(node: nodes.Address, value: bytes) -> str:
        assert len(value) == 32, "Value is not 32 bytes"
        assert int.from_bytes(value, "big") >> 160 == 0, "Value outside type bounds"

        return f"0x{value[-20:].hex()}"

    @classmethod
    def visit_Array(cls, node: nodes.Array, value: bytes) -> list[Any]:
        pass

    @staticmethod
    def visit_Bool(node: nodes.Bool, value: bytes) -> bool:
        pass

    @staticmethod
    def visit_Bytes(node: nodes.Bytes, value: bytes) -> bytes:
        pass

    @staticmethod
    def visit_Fixed(node: nodes.Fixed, value: bytes) -> decimal.Decimal:
        pass

    @staticmethod
    def visit_Integer(node: nodes.Integer, value: bytes) -> int:
        pass

    @staticmethod
    def visit_String(node: nodes.String, value: bytes) -> str:
        pass

    @staticmethod
    def visit_Tuple(node: nodes.Tuple, value: bytes) -> list[Any]:
        pass
