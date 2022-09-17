import decimal

import hypothesis.strategies as st

from eth.codecs.abi import nodes
from eth.codecs.abi.formatter import Formatter
from eth.codecs.abi.parser import Parser


class StrategyMaker:
    """ABI value strategy maker."""

    @classmethod
    def make_strategy(cls, node: nodes.Node) -> st.SearchStrategy:
        """Create a hypothesis search strategy for a given ABI type.

        Parameters:
            node: The ABI type node to generate a strategy for.

        Returns:
            A valid strategy conforming to the ABI type.
        """
        return node.accept(cls)

    @classmethod
    def visit_Address(cls, node: nodes.Address) -> st.SearchStrategy:
        # encoding an address, converts it to an int, decoding does the reverse
        # since 0xAF and 0xaf are the same value in hex, this is fine, however,
        # when comparing strings they are not the same.
        return st.from_regex(r"0x[a-f0-9]{40}", fullmatch=True)

    @classmethod
    def visit_Array(cls, node: nodes.Array) -> st.SearchStrategy:
        st_subtype = cls.make_strategy(node.subtype)
        min_size, max_size = (0, None) if node.size == -1 else (node.size, node.size)
        return st.lists(st_subtype, min_size=min_size, max_size=max_size)

    @staticmethod
    def visit_Bool(node: nodes.Bool) -> st.SearchStrategy:
        return st.booleans()

    @staticmethod
    def visit_Bytes(node: nodes.Bytes) -> st.SearchStrategy:
        min_size, max_size = (0, None) if node.size == -1 else (node.size, node.size)
        return st.binary(min_size=min_size, max_size=max_size)

    @staticmethod
    def visit_Fixed(node: nodes.Fixed) -> st.SearchStrategy:
        # calculate the integer type bounds
        ilo, ihi = 0, 2**node.size - 1
        if node.is_signed:
            subtrahend = 2 ** (node.size - 1)
            ilo, ihi = ilo - subtrahend, ihi - subtrahend

        with decimal.localcontext(decimal.Context(prec=128)):
            # finalize type bound calculation by dividing by scalar 10**-precision
            lo, hi = [decimal.Decimal(v).scaleb(-node.precision) for v in [ilo, ihi]]

        return st.decimals(lo, hi, places=node.precision)

    @staticmethod
    def visit_Integer(node: nodes.Integer) -> st.SearchStrategy:
        lo, hi = 0, 2**node.size - 1
        if node.is_signed:
            subtrahend = 2 ** (node.size - 1)
            lo, hi = lo - subtrahend, hi - subtrahend

        return st.integers(lo, hi)

    @staticmethod
    def visit_String(node: nodes.String) -> st.SearchStrategy:
        return st.text()

    @classmethod
    def visit_Tuple(cls, node: nodes.Tuple) -> st.SearchStrategy:
        inner_strategies = [cls.make_strategy(component) for component in node.components]
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
    return Formatter.format(node), draw(StrategyMaker.make_strategy(node))
