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
from eth.codecs.abi import datatypes


class Formatter:
    @classmethod
    def format(cls, datatype: datatypes.DataType) -> str:
        return datatype.accept(cls)

    @staticmethod
    def visit_Address(_) -> str:
        return "address"

    @classmethod
    def visit_Array(cls, datatype: datatypes.Array) -> str:
        size = "" if datatype.size == -1 else f"{datatype.size}"
        return f"{cls.format(datatype.subtype)}[{size}]"

    @staticmethod
    def visit_Bool(_) -> str:
        return "bool"

    @staticmethod
    def visit_Bytes(datatype: datatypes.Bytes) -> str:
        if datatype.size == -1:
            return "bytes"
        return f"bytes{datatype.size}"

    @staticmethod
    def visit_Fixed(datatype: datatypes.Fixed) -> str:
        prefix = "" if datatype.is_signed else "u"
        return f"{prefix}fixed{datatype.size}x{datatype.precision}"

    @staticmethod
    def visit_Integer(datatype: datatypes.Integer) -> str:
        prefix = "" if datatype.is_signed else "u"
        return f"{prefix}int{datatype.size}"

    @staticmethod
    def visit_String(_) -> str:
        return "string"

    @classmethod
    def visit_Tuple(cls, datatype: datatypes.Tuple) -> str:
        inner = ",".join([cls.format(component) for component in datatype.components])
        return f"({inner})"
