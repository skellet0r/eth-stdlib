import decimal
from itertools import accumulate

import hypothesis.strategies as st
import pytest
from hypothesis import given

import tests.strategies.abi.nodes as st_nodes
from eth.codecs.abi import encode, nodes
from eth.codecs.abi.encoder import Encoder
from eth.codecs.abi.exceptions import EncodeError
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


@given(typestr_and_value(st_nodes.S_Tuple))
def test_encode_static_tuple(value):
    typestr, val = value
    output = encode(typestr, val)

    typs = typestr[1:-1].split(",")
    assert output == b"".join([encode(typ, v) for typ, v in zip(typs, val)])


@given(typestr_and_value(st_nodes.D_Tuple))
def test_encode_dynamic_tuple(value):
    typestr, val = value
    output = encode(typestr, val)

    typs = typestr[1:-1].split(",")

    # encode each component, they go in the tail section
    tail = [encode(typ, v) for typ, v in zip(typs, val)]
    # calculate the offset of each element
    offsets = [0, *accumulate(map(len, tail))][:-1]
    head = b"".join([(len(typs) * 32 + o).to_bytes(32, "big") for o in offsets])

    assert output == head + b"".join(tail)


@given(typestr_and_value(st_nodes.SS_Array))
def test_encode_static_array(value):
    typestr, val = value
    output = encode(typestr, val)

    subtype = typestr.split("[")[0]

    assert output == b"".join([encode(subtype, v) for v in val])


@given(typestr_and_value(st_nodes.DS_Array))
def test_encode_dynamic_array(value):
    typestr, val = value
    output = encode(typestr, val)

    subtype = typestr.split("[")[0]
    expected = len(val).to_bytes(32, "big") + b"".join([encode(subtype, v) for v in val])

    assert output == expected


@given(typestr_and_value(st_nodes.SD_Array))
def test_encode_static_with_dynamic_elements_array(value):
    typestr, val = value
    output = encode(typestr, val)

    subtype = typestr.split("[")[0]
    # encode each component, they go in the tail section
    tail = [encode(subtype, v) for v in val]
    # calculate the offset of each element
    offsets = [0, *accumulate(map(len, tail))][:-1]
    head = b"".join([(len(val) * 32 + o).to_bytes(32, "big") for o in offsets])

    assert output == head + b"".join(tail)


@given(typestr_and_value(st_nodes.DD_Array))
def test_encode_dynamic_with_dynamic_elements_array(value):
    typestr, val = value
    output = encode(typestr, val)

    subtype = typestr.split("[")[0]
    # encode each component, they go in the tail section
    tail = [encode(subtype, v) for v in val]
    # calculate the offset of each element
    offsets = [0, *accumulate(map(len, tail))][:-1]
    head = b"".join([(len(val) * 32 + o).to_bytes(32, "big") for o in offsets])

    assert output == len(val).to_bytes(32, "big") + head + b"".join(tail)


def test_encoding_invalid_node_type_raises():
    with pytest.raises(TypeError, match="Invalid argument type for node"):
        Encoder.encode("foo", "foo")


def test_encoding_invalid_address_value_raises():
    for value in [b"", 123]:
        with pytest.raises(EncodeError, match="Value is not an instance of type 'str'"):
            encode("address", value)

    with pytest.raises(EncodeError, match=r"Value contains non-hexadecimal number\(s\)"):
        encode("address", "0x1234567890abcdefghij1234567890abcdefghij")

    with pytest.raises(EncodeError, match="Value is not 20 bytes"):
        encode("address", "0x1234567890abcdef")


def test_encoding_invalid_array_value_raises():
    with pytest.raises(EncodeError, match=r"Value is not a list \| tuple type"):
        encode("uint256[]", {})

    with pytest.raises(EncodeError, match="Expected value of size 3"):
        encode("uint256[3]", [1, 2])
