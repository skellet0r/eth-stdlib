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

from eth.codecs.abi import datatypes


class Formatter:
    """ABI type AST formatter utilizing the Visitor pattern."""

    @classmethod
    def format(cls, dt: datatypes.DataType) -> str:
        """Format an ABI type AST as a string.

        Returns:
            The ABI type AST represented in string form.
        """

        return dt.accept(cls)

    @staticmethod
    def visit_Address(_) -> str:
        return "address"

    @classmethod
    def visit_Array(cls, dt: datatypes.Array) -> str:
        size = "" if dt.size == -1 else f"{dt.size}"
        return f"{cls.format(dt.subtype)}[{size}]"

    @staticmethod
    def visit_Bool(_) -> str:
        return "bool"

    @staticmethod
    def visit_Bytes(dt: datatypes.Bytes) -> str:
        if dt.is_dynamic:
            return "bytes"
        return f"bytes{dt.size}"

    @staticmethod
    def visit_Fixed(dt: datatypes.Fixed) -> str:
        prefix = "" if dt.is_signed else "u"
        return f"{prefix}fixed{dt.size}x{dt.precision}"

    @staticmethod
    def visit_Integer(dt: datatypes.Integer) -> str:
        prefix = "" if dt.is_signed else "u"
        return f"{prefix}int{dt.size}"

    @staticmethod
    def visit_String(_) -> str:
        return "string"

    @classmethod
    def visit_Tuple(cls, dt: datatypes.Tuple) -> str:
        inner = ",".join([cls.format(component) for component in dt.components])
        return f"({inner})"
