import decimal

import hypothesis.strategies as st
import pytest
from hypothesis import given

import tests.strategies.abi.nodes as st_nodes
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


@given(typestr_and_value(st_nodes.Fixed))
def test_encode_fixed_point(value):
    typestr, val = value
    output = encode(typestr, val)

    precision = int(typestr.rsplit("x", 1)[-1])
    with decimal.localcontext(decimal.Context(prec=128)):
        scaled_val = int(val.scaleb(precision).to_integral_exact())
    assert output == scaled_val.to_bytes(32, "big", signed=not typestr[0] == "u")


@given(typestr_and_value(st_nodes.Integer))
def test_encode_integer(value):
    typestr, val = value
    output = encode(typestr, val)

    assert output == val.to_bytes(32, "big", signed=not typestr[0] == "u")


def test_encode_static_tuple():
    output = encode("(uint8,uint8,uint8)", [1, 2, 3])

    assert output == b"".join(map(lambda v: v.to_bytes(32, "big"), [1, 2, 3]))


def test_encode_dynamic_tuple():
    typestr, value = "(uint8,string,uint8)", [1, "Hello World", 2]
    output = encode(typestr, value)

    expected = b"".join(map(lambda v: v.to_bytes(32, "big"), [1, 0x60, 2, 11]))
    assert output == expected + "Hello World".encode().ljust(32, b"\x00")


def test_encode_static_array():
    output = encode("uint8[3]", [1, 2, 3])

    assert output == b"".join(map(lambda v: v.to_bytes(32, "big"), [1, 2, 3]))


def test_encode_dynamic_array():
    output = encode("uint8[]", [1, 2, 3])

    expected = b"".join(map(lambda v: v.to_bytes(32, "big"), [3, 1, 2, 3]))
    assert output == expected


def test_encode_static_with_dynamic_elements_array():
    output = encode("string[2]", ["Hello", "World"])

    expected = b"".join(map(lambda v: v.to_bytes(32, "big"), [0x40, 0x80, 5]))
    expected += "Hello".encode().ljust(32, b"\x00") + (5).to_bytes(32, "big")
    expected += "World".encode().ljust(32, b"\x00")

    assert output == expected


def test_encode_dynamic_with_dynamic_elements_array():
    output = encode("string[]", ["Hello", "World"])

    expected = b"".join(map(lambda v: v.to_bytes(32, "big"), [2, 0x40, 0x80, 5]))
    expected += "Hello".encode().ljust(32, b"\x00") + (5).to_bytes(32, "big")
    expected += "World".encode().ljust(32, b"\x00")

    assert output == expected
