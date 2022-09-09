import decimal
from itertools import accumulate
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
        try:
            # validate value is a list or tuple of appropriate size
            assert isinstance(value, (list, tuple)), "Value is not a list | tuple type"
            if dt.size != -1:
                assert len(value) == dt.size, f"Expected value of size {dt.size}"
        except AssertionError as e:
            raise EncodeError(Formatter.format(dt), value, e.args[0]) from e

        # similar to tuples, arrays have a head and tail section
        tail = [cls.encode(dt.subtype, val) for val in value]
        if not dt.is_dynamic:
            # a static array with non-dynamic elements
            # is just the concatenation of the encoded elements of the array
            # (b"" in the case of a dynamic array)
            return b"".join(tail)
        elif dt.size == -1 and not dt.subtype.is_dynamic:
            # size of array is dynamic but the elements are not dynamic
            # just return the size + the concatenation of the elements
            return len(value).to_bytes(32, "big") + b"".join(tail)

        # dynamic array with dynamic components
        # width of the head section
        head_width = 32 * len(value)
        # calculate offsets similar to tuple encoding
        offsets = [0, *accumulate(map(len, tail))][:-1]
        head = [(head_width + ofst).to_bytes(32, "big") for ofst in offsets]
        # for a static array we just return the encoded array, since the dynamic
        # elements will have pointers, and static elements will be in-place
        encoded = b"".join(head + tail)
        if dt.size != -1:
            return encoded
        # dynamic arrays we return the size of the array (number of elements)
        # concatenated with the encoded elements
        return len(value).to_bytes(32, "big") + encoded

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
            raise EncodeError(
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
        try:
            # validate value is a list or tuple of appropriate size
            assert isinstance(value, (list, tuple)), "Value is not a list | tuple type"
            assert len(dt.components) == len(value), f"Expected value of size {len(dt.components)}"
        except AssertionError as e:
            raise EncodeError(Formatter.format(dt), value, e.args[0]) from e

        # since tuples are a composite type, they are composed of two sections
        # a head (static) and tail (dynamic). The head is where static data
        # belongs, and the tail is where dynamic data is placed. In the head
        # there will be a pointer to the dynamic section for any component
        # which is dynamic or is composed of dynamic subcomponents (and in the case of array/tuple)
        head, tail = [], []
        for component, val in zip(dt.components, value):
            # if the component is dynamic we place the encoded output
            # in the tail section, and later we will fill the head
            # with the offset to the dynamic data
            output = cls.encode(component, val)
            head.append(None if component.is_dynamic else output)
            tail.append(output if component.is_dynamic else b"")

        # calculate the total width of the head
        # some items like statically sized arrays are placed in the head
        # section and take up more than 1 word
        head_width = sum([32 if val is None else len(val) for val in head])
        # calculate the offset from the start of the tail section for each
        # element in the tail section. i.e. the first element starts at
        # index 0, whereas the last element starts at index (sum(map(len, tail[:-1])))
        # when added with the head width, we have the exact offset position of a
        # dynamic piece of data in the tail section
        offsets = [0, *accumulate(map(len, tail))][:-1]
        # recompute the head, replacing None with the exact offset of the dynamic data
        new_head = [
            (head_width + ofst).to_bytes(32, "big") if val is None else val
            for val, ofst in zip(head, offsets)
        ]
        # concatenate the head and tail together
        return b"".join(new_head + tail)
