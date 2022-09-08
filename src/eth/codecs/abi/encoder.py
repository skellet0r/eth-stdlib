from typing import Any

from eth.codecs.abi import datatypes


class Encoder:
    def __init__(self, datatype: datatypes.DataType):
        self.datatype = datatypes

    def encode(self, value: Any) -> bytes:
        return self.datatype.accept(self, value)
