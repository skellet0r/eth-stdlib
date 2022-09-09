from typing import Any

from eth.codecs.abi.encoder import Encoder
from eth.codecs.abi.parser import Parser


def encode(typestr: str, value: Any) -> bytes:
    typ = Parser.parse(typestr)
    return Encoder.encode(typ, value)
