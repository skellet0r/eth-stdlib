from hypothesis import given

from eth.codecs.abi.nodes import ArrayNode, TupleNode
from eth.codecs.abi.strategies.nodes import Array, Tuple


@given(Array)
def test_top_level_is_always_array(node):
    assert isinstance(node, ArrayNode)


@given(Tuple)
def test_top_level_is_always_tuple(node):
    assert isinstance(node, TupleNode)
