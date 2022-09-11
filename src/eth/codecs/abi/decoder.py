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
