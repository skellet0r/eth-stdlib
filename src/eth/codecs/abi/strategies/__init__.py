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

from typing import Any, Optional, Tuple

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
def schema_and_value(
    draw: st.DrawFn, st_type: Optional[st.SearchStrategy] = None
) -> Tuple[str, Any]:
    """Generate a valid ABI schema and an encodable value for it.

    Parameters:
        st_type: An ABI node type search strategy.

    Returns:
        A tuple containing the valid ABI type string and the encodable value for the type string.
    """
    typestr = draw(schema) if st_type is None else str(draw(st_type))
    return (typestr, draw(value(typestr)))
