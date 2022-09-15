import decimal
import re

import hypothesis.strategies as st

from eth.codecs.abi import nodes


class StrategyCreator:
    """ABI value strategy creator."""

    ADDRESS_PATTERN = re.compile(r"0x[a-f0-9]", re.IGNORECASE)

    @classmethod
    def create(cls, node: nodes.Node) -> st.SearchStrategy:
        """Create a hypothesis search strategy for a given ABI type.

        Parameters:
            node: The ABI type node to generate a strategy for.

        Returns:
            A valid strategy conforming to the ABI type.
        """
        return node.accept(cls)

    @classmethod
    def visit_Address(cls, node: nodes.Address) -> st.SearchStrategy:
        return st.from_regex(cls.ADDRESS_PATTERN, fullmatch=True)

    @classmethod
    def visit_Array(cls, node: nodes.Array) -> st.SearchStrategy:
        st_subtype = cls.create(node.subtype)
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
        inner_strategies = [cls.create(component) for component in node.components]
        return st.tuples(*inner_strategies)
