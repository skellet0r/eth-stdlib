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

import re

from eth.codecs.abi import nodes
from eth.codecs.abi.exceptions import ParseError


class Parser:
    """Ethereum contract ABI schema parser.

    Attributes:
        ARRAY_PATTERN: compiled regex for matching array schemas.
        TUPLE_PATTERN: compiled regex for matching tuple schemas.
        VALUE_PATTERN: compiled regex for matching value schemas:

            * fixed-width byte arrays
            * integers
            * fixed-point decimals
    """

    ARRAY_PATTERN = re.compile(r"(.+)\[(\d*)\]")
    TUPLE_PATTERN = re.compile(r"\(.+\)")
    VALUE_PATTERN = re.compile(r"bytes(\d+)|u?(?:fixed(\d+)x(\d+)|int(\d+))")

    @classmethod
    def parse(cls, schema: str) -> nodes.ABITypeNode:
        """Parse an ABI schema into a AST.

        Parameters:
            schema: an ABI type string, such as:
                * 'uint256'
                * '(bytes32,ufixed128x10)'

        Returns:
            An AST-like strucutre representing the type string.

        Raises:
            ParseError: If ``schema`` contains an invalid ABI type.
        """
        # simplest types to match against since they don't require regex
        match schema:
            case "address":
                return nodes.AddressNode()
            case "bool":
                return nodes.BooleanNode()
            case "bytes":
                return nodes.BytesNode()
            case "string":
                return nodes.StringNode()
            case "()":
                return nodes.TupleNode(())

        # using fullmatch method to correctly match against the entire string
        if (mo := cls.VALUE_PATTERN.fullmatch(schema)) is not None:
            # identify which type was matched, and validate it
            match mo.lastindex:
                case 1:  # bytes
                    if (size := int(mo[1])) not in range(1, 33):
                        raise ParseError(schema, f"'{size}' is not a valid byte array width")
                    return nodes.BytesNode(size)
                case 3:  # fixed
                    if (size := int(mo[2])) not in range(8, 264, 8):
                        raise ParseError(schema, f"'{size}' is not a valid fixed point width")
                    elif (precision := int(mo[3])) not in range(81):
                        raise ParseError(
                            schema, f"'{precision}' is not a valid fixed point precision"
                        )
                    return nodes.FixedNode(size, precision, schema[0] != "u")
                case _:  # integer
                    if (size := int(mo[4])) not in range(8, 264, 8):
                        raise ParseError(schema, f"'{size}' is not a valid integer width")
                    return nodes.IntegerNode(size, schema[0] != "u")

        # array
        elif (mo := cls.ARRAY_PATTERN.fullmatch(schema)) is not None:
            etype, asize = cls.parse(mo[1]), int(mo[2]) if mo[2] else None
            if asize == 0:
                raise ParseError(schema, "'0' is not a valid array size")
            elif isinstance(etype, nodes.TupleNode) and len(etype.ctypes) == 0:
                raise ParseError(schema, "'()' is not a valid array element type")
            return nodes.ArrayNode(etype, asize)

        # tuple
        elif cls.TUPLE_PATTERN.fullmatch(schema) is not None:
            # goal: split the type string on commas while preserving any component tuples
            components, compstr = [], schema[1:-1]
            depth, lastpos = 0, 0  # keep track of nested tuples
            for mo in re.finditer(r"\(|\)|,", compstr):
                match mo[0]:
                    case "(":  # tuple start
                        depth += 1
                    case ")":  # tuple end
                        depth -= 1
                    case _ if depth == 0:  # component separator
                        # append the component substring from lastpos up to the comma
                        components.append(compstr[lastpos : mo.start()])
                        lastpos = mo.end()  # set lastpos after the comma

            # append the remaining component after the last comma
            components.append(compstr[lastpos:])
            # validate we have no empty components (dangling commas)
            if "" in components:
                raise ParseError(schema, "Dangling comma detected in type string")

            ctypes = tuple((cls.parse(component) for component in components))
            if any((isinstance(typ, nodes.TupleNode) and len(typ.ctypes) == 0 for typ in ctypes)):
                raise ParseError(schema, "Empty tuples are disallowed as components")

            # recurse and parse components
            return nodes.TupleNode(ctypes)

        # none of the above matching was successful, raise since we can't parse `schema`
        raise ParseError(schema, "ABI type not parseable")
