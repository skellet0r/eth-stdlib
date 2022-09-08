import decimal
from collections.abc import Sequence
from typing import Any

from eth.codecs.abi import datatypes


class Encoder:
    @classmethod
    def encode(cls, datatype: datatypes.DataType, value: Any) -> bytes:
        return datatype.accept(cls, value)

    @staticmethod
    def visit_Address(_, value: str) -> bytes:
        pass

    @classmethod
    def visit_Array(cls, dt: datatypes.Array, value: Sequence) -> bytes:
        pass

    @staticmethod
    def visit_Bool(_, value: bool) -> bytes:
        pass

    @staticmethod
    def visit_Bytes(dt: datatypes.Bytes, value: bytes) -> bytes:
        pass

    @staticmethod
    def visit_Fixed(dt: datatypes.Fixed, value: decimal.Decimal) -> bytes:
        pass

    @staticmethod
    def visit_Integer(dt: datatypes.Integer, value: int) -> bytes:
        pass

    @classmethod
    def visit_String(cls, _, value: str) -> bytes:
        pass

    @classmethod
    def visit_Tuple(cls, dt: datatypes.Tuple, value: Sequence) -> bytes:
        pass
