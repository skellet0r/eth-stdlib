from hypothesis import example, given

import tests.strategies.abi.nodes as st_nodes
from eth.codecs.abi import decode, encode
from tests.strategies.abi.values import typestr_and_value


@given(typestr_and_value(st_nodes.Atomic))
def test_decoding_encoded_atomic_values(value):
    typestr, val = value

    assert decode(typestr, encode(typestr, val)) == val


@given(typestr_and_value(st_nodes.Array | st_nodes.Tuple))
@example(("((string,string))", (("", ""),)))
@example(("(uint256[3])", ([1, 2, 3],)))
def test_decoding_encoded_composite_values(value):
    typestr, val = value

    assert decode(typestr, encode(typestr, val)) == val
