import decimal

import pytest
from hypothesis import example, given

from eth.codecs.abi import decode, encode
from eth.codecs.abi.decoder import Decoder
from eth.codecs.abi.exceptions import DecodeError
from eth.codecs.abi.nodes import IntegerNode
from eth.codecs.abi.strategies import schema_and_value as st_schema_and_value


@given(st_schema_and_value())
@example(("((uint256,uint256))", ((1, 1),)))
@example(("((string,string))", (("", ""),)))
@example(("(uint256[3])", ([1, 2, 3],)))
@example(("(uint256[])", ([1, 2, 3],)))
@example(("string[]", [""]))
@example(("ufixed128x10", decimal.Decimal("1.2")))
@example(("int128", -1))
@example(("()", ()))
def test_decoding(value):
    typestr, val = value

    assert decode(typestr, encode(typestr, val)) == val


def test_decoding_disable_checksum():
    value = b"\x00" * 12 + bytes.fromhex("Cd2a3d9f938e13Cd947eC05ABC7fe734df8DD826")
    assert decode("address", value, checksum=False) == "0xcd2a3d9f938e13cd947ec05abc7fe734df8dd826"


def test_decode_raises_for_invalid_arguments():
    for args in [({}, b""), (IntegerNode(256, False), {})]:
        with pytest.raises(TypeError, match=r"Received invalid type '\w+' for parameter '\w+'"):
            Decoder.decode(*args)


def test_validate_atom_raises_for_invalid_values():
    with pytest.raises(DecodeError, match="Value is not 32 bytes"):
        Decoder.validate_atom(IntegerNode(256, False), b"", 256)

    with pytest.raises(DecodeError, match="Value outside type bounds"):
        Decoder.validate_atom(IntegerNode(128, False), (2**128).to_bytes(32, "big"), 8)


def test_decode_array_raises_for_invalid_value():
    with pytest.raises(DecodeError, match="Dynamic array value has invalid length"):
        decode("uint256[]", b"")

    with pytest.raises(DecodeError, match="Expected 32 bytes, received 0 bytes."):
        decode("uint256[1]", b"")

    with pytest.raises(DecodeError, match="Invalid array size"):
        decode("uint256[2]", b"\x01" * 65)

    with pytest.raises(DecodeError, match="Expected 32 bytes, received 64 bytes"):
        decode("uint256[]", b"\x00" * 64)


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
    with pytest.raises(DecodeError, match="expected size of 32 bytes"):
        decode("(uint256)", b"")

    with pytest.raises(DecodeError, match="Value length is less than expected"):
        decode("(uint256[])", b"")
