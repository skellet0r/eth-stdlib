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

from eth.codecs.abi import nodes


class Formatter:
    """ABI type AST/node formatter implementing the visitor pattern."""

    @classmethod
    def format(cls, node: nodes.Node) -> str:
        """Format an ABI type AST/node as a string.

        Parameters:
            node: The node to format.

        Returns:
            The ABI type AST/node represented in string form.

        Raises:
            TypeError: If node argument is not an instance of `nodes.Node`.
        """
        if not isinstance(node, nodes.Node):
            raise TypeError(f"Invalid argument type for node: {type(node).__qualname__!r}")

        return node.accept(cls)

    @staticmethod
    def visit_Address(_) -> str:
        return "address"

    @classmethod
    def visit_Array(cls, node: nodes.Array) -> str:
        size = "" if node.size == -1 else f"{node.size}"
        return f"{cls.format(node.subtype)}[{size}]"

    @staticmethod
    def visit_Bool(_) -> str:
        return "bool"

    @staticmethod
    def visit_Bytes(node: nodes.Bytes) -> str:
        if node.is_dynamic:
            return "bytes"
        return f"bytes{node.size}"

    @staticmethod
    def visit_Fixed(node: nodes.Fixed) -> str:
        prefix = "" if node.is_signed else "u"
        return f"{prefix}fixed{node.size}x{node.precision}"

    @staticmethod
    def visit_Integer(node: nodes.Integer) -> str:
        prefix = "" if node.is_signed else "u"
        return f"{prefix}int{node.size}"

    @staticmethod
    def visit_String(_) -> str:
        return "string"

    @classmethod
    def visit_Tuple(cls, node: nodes.Tuple) -> str:
        inner = ",".join([cls.format(component) for component in node.components])
        return f"({inner})"
