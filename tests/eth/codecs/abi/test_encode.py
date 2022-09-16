import hypothesis.strategies as st
import pytest
from hypothesis import given

from eth.codecs.abi import encode, nodes
from tests.strategies.abi.values import strategy, typestr_and_value


@given(strategy("address"))
def test_encode_address(value):
    assert encode("address", value) == int(value, 16).to_bytes(32, "big")


@pytest.mark.parametrize("value", [False, True])
def test_encode_bool(value):
    assert encode("bool", value) == value.to_bytes(32, "big")


@given(strategy("bytes"))
def test_encode_bytes(value):
    output = encode("bytes", value)

    if (length := len(value)) % 32 != 0:
        width = length + 32 - (length % 32)
        value = value.ljust(width, b"\x00")
    assert output == length.to_bytes(32, "big") + value


@given(strategy("string"))
def test_encode_string(value):
    output = encode("string", value)

    # string encoding under the hood uses bytes encoding
    value = value.encode()
    if (length := len(value)) % 32 != 0:
        width = length + 32 - (length % 32)
        value = value.ljust(width, b"\x00")
    assert output == length.to_bytes(32, "big") + value


@given(typestr_and_value(st.builds(nodes.Bytes, st.integers(1, 32))))
def test_encode_static_bytes(value):
    typestr, val = value
    assert encode(typestr, val) == val.ljust(32, b"\x00")
