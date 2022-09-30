import functools

import hypothesis.strategies as st

from eth.codecs.abi import nodes
from eth.codecs.abi.parser import Parser


class StrategyMaker:
    """ABI value strategy maker."""

    @classmethod
    @functools.cache
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
        return st.from_regex(r"0x[a-f0-9]{40}", fullmatch=True)

    @classmethod
    def visit_ArrayNode(cls, node: nodes.ArrayNode) -> st.SearchStrategy:
        st_subtype = cls.make_strategy(node.etype)
        min_size, max_size = (0, None) if node.length == -1 else (node.length, node.length)
        return st.lists(st_subtype, min_size=min_size, max_size=max_size)

    @staticmethod
    def visit_BoolNode(node: nodes.BooleanNode) -> st.SearchStrategy:
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


@st.composite
def strategy(draw: st.DrawFn, typestr: str | st.SearchStrategy):
    """Generate a valid ABI encodable value for a given type string.

    Parameters:
        typestr: A valid ABI type string, or an ABI node strategy.

    Returns:
        A valid ABI encodable value for the given type string.
    """
    if isinstance(typestr, str):
        # user provided typestr
        return draw(StrategyMaker.make_strategy(Parser.parse(typestr)))
    return draw(StrategyMaker.make_strategy(draw(typestr)))


@st.composite
def typestr_and_value(draw: st.DrawFn, st_node: st.SearchStrategy):
    node = draw(st_node)
    return str(node), draw(StrategyMaker.make_strategy(node))
