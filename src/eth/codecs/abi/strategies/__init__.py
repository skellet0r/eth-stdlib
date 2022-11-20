from typing import Any

import hypothesis.strategies as st

from eth.codecs.abi.parser import Parser
from eth.codecs.abi.strategies.nodes import Node as st_node
from eth.codecs.abi.strategies.values import StrategyMaker

schema = st.builds(str, st_node)


@st.composite
def value(draw: st.DrawFn, schema: str) -> Any:
    """Generate a valid ABI encodable value for a given type string.

    Parameters:
        schema: A valid ABI type string.

    Returns:
        A valid ABI encodable value for the given type string.
    """
    return draw(StrategyMaker.make_strategy(Parser.parse(schema)))


@st.composite
def schema_and_value(draw: st.DrawFn, st_type: st.SearchStrategy | None = None) -> tuple[str, Any]:
    """Generate a valid ABI schema and an encodable value for it.

    Parameters:
        st_type: An ABI node type search strategy.

    Returns:
        A tuple containing the valid ABI type string and the encodable value for the type string.
    """
    typestr = draw(schema) if st_type is None else str(draw(st_type))
    return (typestr, draw(value(typestr)))
