# This file is part of the eth-stdlib library.
# Copyright (C) 2022 Edward Amor
#
# The eth-stdlib library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# The eth-stdlib library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from typing import Any


class ABIError(Exception):
    """Base exception class for errors."""


class ParseError(ABIError):
    """Raised when attempting to parse an invalid type string.

    Parameters:
        where: The invalid type string.
        msg: Explanation of why the type string is invalid.
        *args: Additional arguments passed to the parent class init method.
        **kwargs: Additional keyword arguments passed to the parent class init method.

    Attributes:
        where: The invalid type string.
        msg: Explanation of why the type string is invalid.
    """

    def __init__(self, where: str, msg: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.where = where
        self.msg = msg

    def __str__(self) -> str:
        return f"Error at {self.where!r} - {self.msg}"


class CodecError(ABIError):
    """Base class for codec errors.

    Parameters:
        typestr: The type string of the type coding was attempted for.
        value: The value that coding was attempted for.
        msg: Explanation of why the value is invalid.
        *args: Additional arguments passed to the parent class init method.
        **kwargs: Additional keyword arguments passed to the parent class init method.

    Attributes:
        typestr: The type string of the type coding was attempted for.
        value: The value that coding was attempted for.
        msg: Explanation of why the value is invalid.
    """

    def __init__(self, typestr: str, value: Any, msg: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.typestr = typestr
        self.value = value
        self.msg = msg


class EncodeError(CodecError):
    """Raised when attempting to encode an invalid value for a type."""

    def __str__(self) -> str:
        return f"Error encoding {self.value!r} as {self.typestr!r} - {self.msg}"


class DecodeError(CodecError):
    """Raised when attempting to decode an invalid value for a type."""

    def __str__(self) -> str:
        return f"Error decoding {self.value!r} as {self.typestr!r} - {self.msg}"
