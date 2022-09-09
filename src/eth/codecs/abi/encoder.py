import decimal
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
    def visit_Array(cls, dt: datatypes.Array, value: list | tuple) -> bytes:
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
        typestr = Formatter.format(dt)
        if not isinstance(value, decimal.Decimal):
            raise EncodeError(typestr, value, "Value is not an instance of type 'decimal.Decimal'")

        # calculate the type bounds
        with decimal.localcontext(decimal.Context(prec=128)) as ctx:
            scalar = decimal.Decimal(10).scaleb(-dt.precision)  # 10 ** -precision
            lo, hi = decimal.Decimal(0), decimal.Decimal(2**dt.size - 1) * scalar
            if dt.is_signed:
                lo, hi = (
                    decimal.Decimal(-(2 ** (dt.size - 1))) * scalar,
                    decimal.Decimal(2 ** (dt.size - 1) - 1) * scalar,
                )

            try:
                assert lo <= value <= hi, "Value outside type bounds"
                # take care of negative values here, they imply that dt.is_signed is True
                scaled_value = int(value.scaleb(dt.precision).to_integral_exact()) % 2**dt.size
                # using to_integral_exact will signal Inexact if non-zero digits were rounded off
                # https://docs.python.org/3/library/decimal.html#decimal.Decimal.to_integral_exact
                assert not ctx.flags[decimal.Inexact], "Precision of value is greater than allowed"
            except AssertionError as e:
                raise EncodeError(typestr, value, e.args[0]) from e

        if value < 0:  # implies dt.is_signed is True
            width = (scaled_value.bit_length() + 7) // 8
            return scaled_value.to_bytes(width, "big").rjust(32, b"\xff")
        return scaled_value.to_bytes(32, "big")

    @staticmethod
    def visit_Integer(dt: datatypes.Integer, value: int) -> bytes:
        # calculate type bounds
        lo, hi = 0, 2**dt.size - 1
        if dt.is_signed:
            lo, hi = -(2 ** (dt.size - 1)), 2 ** (dt.size - 1) - 1

        try:
            # validate value fits in type and is of type int
            assert lo <= value <= hi, "Value outside type bounds"
            assert isinstance(value, int), "Value not an instance of type 'int'"
        except AssertionError as e:
            # value can be a float, in which case it's not valid
            raise EncodeError(Formatter.format(dt), value, e.args[0]) from e
        except TypeError as e:
            raise TypeError(
                Formatter.format(dt), value, "Value not an instance of type 'int'"
            ) from e

        return value.to_bytes(32, "big", signed=dt.is_signed)

    @classmethod
    def visit_String(cls, _, value: str) -> bytes:
        try:
            return cls.encode(datatypes.Bytes(-1), value.encode())
        except (AttributeError, EncodeError) as e:
            # AttributeError - if value does not have encode method
            # EncodeError - if value.encode() does not return a bytes | bytearray instance
            raise EncodeError("string", value, "Value is not an instance of type 'str'") from e

    @classmethod
    def visit_Tuple(cls, dt: datatypes.Tuple, value: list | tuple) -> bytes:
        pass
