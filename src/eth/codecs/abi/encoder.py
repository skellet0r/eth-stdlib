import decimal
from collections.abc import Sequence
from typing import Any

from eth.codecs.abi import datatypes
from eth.codecs.abi.exceptions import EncodeError
from eth.codecs.abi.formatter import Formatter


class Encoder:
    @classmethod
    def encode(cls, datatype: datatypes.DataType, value: Any) -> bytes:
        return datatype.accept(cls, value)

    @staticmethod
    def visit_Address(_, value: str) -> bytes:
        try:
            bval = bytes.fromhex(value.removeprefix("0x"))
            assert len(bval) == 20
            return bval.rjust(32, b"\x00")
        except (AttributeError, TypeError) as e:
            # AttributeError - if `value` does not have `removeprefix` method (only bytes | str)
            # TypeError - if `value` is not a `str` instance (if value == bytes)
            raise EncodeError("address", value, "Value is not an instance of type 'str'") from e
        except ValueError as e:
            # ValueError - if value contains non-hexadecimal characters (e.g "-0x...", "0xSJ32...")
            raise EncodeError("address", value, "Value contains non-hexadecimal number(s)") from e
        except AssertionError as e:
            # AssertionError - if length of the bytes value is not 20
            raise EncodeError("address", value, "Value is not 20 bytes") from e

    @classmethod
    def visit_Array(cls, dt: datatypes.Array, value: Sequence) -> bytes:
        pass

    @staticmethod
    def visit_Bool(_, value: bool) -> bytes:
        try:
            assert isinstance(value, bool), "Value is not an instance of type 'bool'"
            return value.to_bytes(32, "big")
        except AssertionError as e:
            raise EncodeError("bool", value, e.args[0]) from e

    @staticmethod
    def visit_Bytes(dt: datatypes.Bytes, value: bytes) -> bytes:
        try:
            assert isinstance(value, (bytes, bytearray)), "Value is not an instance of type 'bytes'"
            length = len(value)
            if not dt.is_dynamic:
                assert length <= dt.size, f"Value is not {dt.size} bytes"
        except AssertionError as e:
            raise EncodeError(Formatter.format(dt), value, e.args[0]) from e

        # dyanmic
        if dt.is_dynamic:
            if length % 32 != 0:
                # pad end with null bytes up to nearest word
                width = length + 32 - (length % 32)
                value = value.ljust(width, b"\x00")
            return length.to_bytes(32, "big") + value

        # static
        return value.rjust(dt.size, b"\x00").ljust(32, b"\x00")

    @staticmethod
    def visit_Fixed(dt: datatypes.Fixed, value: decimal.Decimal) -> bytes:
        pass

    @staticmethod
    def visit_Integer(dt: datatypes.Integer, value: int) -> bytes:
        pass

    @classmethod
    def visit_String(cls, _, value: str) -> bytes:
        try:
            return cls.encode(datatypes.Bytes(-1), value.encode())
        except (AttributeError, EncodeError) as e:
            # AttributeError - if value does not have encode method
            # EncodeError - if value.encode() does not return a bytes | bytearray instance
            raise EncodeError("string", value, "Value is not an instance of type 'str'")

    @classmethod
    def visit_Tuple(cls, dt: datatypes.Tuple, value: Sequence) -> bytes:
        pass
