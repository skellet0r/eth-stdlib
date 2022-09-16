import pytest
from hypothesis import given

from eth.codecs.abi.formatter import Formatter
from eth.codecs.abi.nodes import Address, Bool, Bytes, Fixed, Integer, String
from tests.strategies.abi import nodes as st_nodes


@pytest.mark.parametrize("typ,result", [(Address, "address"), (Bool, "bool"), (String, "string")])
def test_format_non_parametrized_nodes(typ, result):
    assert Formatter.format(typ()) == result


@pytest.mark.parametrize("size", range(-5, 5))
def test_format_bytes(size):
    expected = "bytes" if size == -1 else f"bytes{size}"
    assert Formatter.format(Bytes(size)) == expected


@pytest.mark.parametrize("bits,prec,is_signed", zip([-10, 32], [80, -8], [False, True]))
def test_format_fixed(bits, prec, is_signed):
    expected = f"{'' if is_signed else 'u'}fixed{bits}x{prec}"
    assert Formatter.format(Fixed(bits, prec, is_signed)) == expected


@pytest.mark.parametrize("bits,is_signed", zip(range(-5, 5), [False, True] * 5))
def test_format_integer(bits, is_signed):
    expected = f"{'' if is_signed else 'u'}int{bits}"
    assert Formatter.format(Integer(bits, is_signed)) == expected


@given(st_nodes.Array)
def test_format_array(node):
    suffix = "[]" if node.size == -1 else f"[{node.size}]"

    assert Formatter.format(node) == Formatter.format(node.subtype) + suffix


@given(st_nodes.Tuple)
def test_format_tuple(node):
    inner = ",".join(Formatter.format(c) for c in node.components)

    assert Formatter.format(node) == f"({inner})"
