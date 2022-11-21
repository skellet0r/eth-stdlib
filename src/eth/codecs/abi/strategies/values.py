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

import functools

import hypothesis.strategies as st

from eth.codecs.abi import nodes
from eth.codecs.utils import checksum_encode


class StrategyMaker:
    """ABI value strategy maker."""

    @classmethod
    @functools.lru_cache(maxsize=None)
    def make_strategy(cls, node: nodes.ABITypeNode) -> st.SearchStrategy:
        """Create a hypothesis search strategy for a given ABI type.

        Parameters:
            node: The ABI type node to generate a strategy for.

        Returns:
            A valid strategy conforming to the ABI type.
        """
        return node.accept(cls)

    @classmethod
    def visit_AddressNode(cls, node: nodes.AddressNode) -> st.SearchStrategy:
        # encoding an address, converts it to an int, decoding does the reverse
        # since 0xAF and 0xaf are the same value in hex, this is fine, however,
        # when comparing strings they are not the same.
        return st.builds(checksum_encode, st.from_regex(r"0x[a-f0-9]{40}", fullmatch=True))

    @classmethod
    def visit_ArrayNode(cls, node: nodes.ArrayNode) -> st.SearchStrategy:
        st_subtype = cls.make_strategy(node.etype)
        min_size, max_size = (0, None) if node.length is None else (node.length, node.length)
        return st.lists(st_subtype, min_size=min_size, max_size=max_size)

    @staticmethod
    def visit_BooleanNode(node: nodes.BooleanNode) -> st.SearchStrategy:
        return st.booleans()

    @staticmethod
    def visit_BytesNode(node: nodes.BytesNode) -> st.SearchStrategy:
        min_size, max_size = (0, None) if node.size is None else (node.size, node.size)
        return st.binary(min_size=min_size, max_size=max_size)

    @staticmethod
    def visit_FixedNode(node: nodes.FixedNode) -> st.SearchStrategy:
        # calculate the integer type bounds
        return st.decimals(*node.bounds, places=node.precision)

    @staticmethod
    def visit_IntegerNode(node: nodes.IntegerNode) -> st.SearchStrategy:
        return st.integers(*node.bounds)

    @staticmethod
    def visit_StringNode(node: nodes.StringNode) -> st.SearchStrategy:
        return st.text()

    @classmethod
    def visit_TupleNode(cls, node: nodes.TupleNode) -> st.SearchStrategy:
        inner_strategies = [cls.make_strategy(ctyp) for ctyp in node.ctypes]
        return st.tuples(*inner_strategies)
