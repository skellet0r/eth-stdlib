from hypothesis import given

from eth.codecs.abi.formatter import Formatter
from eth.codecs.abi.parser import Parser
from tests.strategies.abi.nodes import Composite


@given(Composite)
def test_parser(node):
    # generate a random valid abi type node format as typestr and then parse it
    assert Parser.parse(Formatter.format(node)) == node
