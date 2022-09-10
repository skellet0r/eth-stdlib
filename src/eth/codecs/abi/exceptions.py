"""This file is part of the eth-stdlib library.
Copyright (C) 2022  Edward Amor

The eth-stdlib library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The eth-stdlib library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Any


class ABIError(Exception):
    ...


class ParseError(ABIError):
    def __init__(self, where: str, msg: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.where = where
        self.msg = msg

    def __str__(self) -> str:
        return f"Error at {self.where!r} - {self.msg}"


class EncodeError(ABIError):
    def __init__(self, typestr: str, value: Any, msg: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.typestr = typestr
        self.value = value
        self.msg = msg

    def __str__(self) -> str:
        return f"Error encoding {self.value!r} as {self.typestr!r} - {self.msg}"
