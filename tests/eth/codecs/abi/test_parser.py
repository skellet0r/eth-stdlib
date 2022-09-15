import hypothesis.strategies as st
import pytest
from hypothesis import assume, given, settings

from eth.codecs.abi.exceptions import ParseError
from eth.codecs.abi.formatter import Formatter
from eth.codecs.abi.parser import Parser
from tests.strategies.abi.nodes import Node


@given(Node)
def test_parser(node):
    # generate a random valid abi type node format as typestr and then parse it
    assert Parser.parse(Formatter.format(node)) == node


@pytest.mark.parametrize("typestr", ["bytes1233", "bytes592309", "bytes8193"])
def test_parse_invalid_bytes_typestr_raises(typestr):
    with pytest.raises(ParseError, match=r"'\d+' is not a valid byte array width"):
        Parser.parse(typestr)


@pytest.mark.parametrize("typestr", ["fixed127x30", "ufixed189x25", "fixed99992323x32"])
def test_parse_invalid_bits_in_fixed_point_typestr_raises(typestr):
    with pytest.raises(ParseError, match=r"'\d+' is not a valid fixed point width"):
        Parser.parse(typestr)


@pytest.mark.parametrize("typestr", ["ufixed128x92", "fixed256x100000", "fixed8x000010123"])
def test_parse_invalid_precision_in_fixed_point_typestr_raises(typestr):
    with pytest.raises(ParseError, match=r"'\d+' is not a valid fixed point precision"):
        Parser.parse(typestr)


@pytest.mark.parametrize("typestr", ["int12888", "uint00123213", "int79238", "int64001"])
def test_parse_invalid_integer_typestr_raises(typestr):
    with pytest.raises(ParseError, match=r"'\d+' is not a valid integer width"):
        Parser.parse(typestr)


def test_parse_invalid_array_typestr_raises():
    with pytest.raises(ParseError, match=r"'0' is not a valid array size"):
        Parser.parse("uint256[0]")


def test_parse_invalid_tuple_typestr_raises():
    with pytest.raises(ParseError, match=r"Dangling comma detected in type string"):
        Parser.parse("(aa,bb,)")


@settings(max_examples=5)
@given(st.text(max_size=128))
def test_parse_invalid_typestr_raises(typestr):
    assume(typestr not in ("bytes", "string", "address", "bool"))
    assume(all(typ not in typestr for typ in ("uint", "int", "ufixed", "fixed")))

    with pytest.raises(ParseError, match="ABI type not parseable"):
        Parser.parse(typestr)
