import decimal

import pytest
from hypothesis import example, given

import tests.strategies.abi.nodes as st_nodes
from eth.codecs.abi import decode, encode
from eth.codecs.abi.decoder import Decoder
from eth.codecs.abi.exceptions import DecodeError
from eth.codecs.abi.nodes import Integer
from tests.strategies.abi.values import typestr_and_value


@given(typestr_and_value(st_nodes.Node))
@example(("((uint256,uint256))", ((1, 1),)))
@example(("((string,string))", (("", ""),)))
@example(("(uint256[3])", ([1, 2, 3],)))
@example(("(uint256[])", ([1, 2, 3],)))
@example(("string[]", [""]))
@example(("ufixed128x10", decimal.Decimal("1.2")))
@example(("int128", -1))
def test_decoding(value):
    typestr, val = value

    assert decode(typestr, encode(typestr, val)) == val


def test_decode_raises_for_invalid_arguments():
    for args in [({}, b""), (Integer(256, False), {})]:
        with pytest.raises(TypeError, match=r"Received invalid type '\w+' for parameter '\w+'"):
            Decoder.decode(*args)


def test_validate_atom_raises_for_invalid_values():
    with pytest.raises(DecodeError, match="Value is not 32 bytes"):
        Decoder.validate_atom(Integer(256, False), b"", 256)

    with pytest.raises(DecodeError, match="Value outside type bounds"):
        Decoder.validate_atom(Integer(128, False), (2**128).to_bytes(32, "big"), 8)


def test_decode_array_raises_for_invalid_value():
    with pytest.raises(DecodeError, match="Dynamic array value invalid size"):
        decode("uint256[]", b"")

    with pytest.raises(DecodeError, match="Static array value invalid size"):
        decode("uint256[1]", b"")

    with pytest.raises(DecodeError, match="Invalid array size"):
        decode("uint256[2]", b"\x01" * 65)


@pytest.mark.parametrize("typestr", ["bytes", "string"])
def test_decode_bytes_and_string_raises_for_invalid_value(typestr):
    with pytest.raises(DecodeError, match="Invalid size for dynamic bytes"):
        decode(typestr, b"")

    with pytest.raises(DecodeError, match="Data section is not the correct size"):
        decode(typestr, b"\x00" * 31 + b"\x01")


@pytest.mark.parametrize("typestr", ["ufixed128x10", "uint8"])
def test_decode_integer_and_fixed_raises_for_invalid_value(typestr):
    with pytest.raises(DecodeError, match="Value is not 32 bytes"):
        decode(typestr, b"\x00" * 33)

    with pytest.raises(DecodeError, match="Value is outside type bounds"):
        decode(typestr, b"\xff" * 31 + b"\xfe")


def test_decode_tuple_raises_for_invalid_value():
    with pytest.raises(DecodeError, match="Value length is less than expected"):
        decode("(uint256)", b"")
