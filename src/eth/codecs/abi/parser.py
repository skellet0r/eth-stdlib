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

from eth.codecs.abi import datatypes
from eth.codecs.abi.exceptions import ParseError


class Parser:
    """Ethereum ABI type string parser.

    Attributes:
        ARRAY_PATTERN: compiled regex for matching array type strings.
        TUPLE_PATTERN: compiled regex for matching tuple type strings.
        VALUE_PATTERN: compiled regex for matching value type strings 'bytesN', 'uintN', 'intN',
            'ufixedMxN', and 'fixedMxN'.
    """

    ARRAY_PATTERN = re.compile(r"(.+)\[(\d*)\]")
    TUPLE_PATTERN = re.compile(r"\(.+\)")
    VALUE_PATTERN = re.compile(r"bytes(\d+)|u?(?:fixed(\d+)x(\d+)|int(\d+))")

    @classmethod
    def parse(cls, typestr: str) -> datatypes.DataType:
        """Parse a type string into a AST-like strucutre.

        Parameters:
            typestr: an ABI type string (i.e. 'uint256', '(bytes32[],ufixed128x10)').

        Returns:
            An AST-like strucutre representing the type string.

        Raises:
            ParseError: If `typestr`, or a component type string of it, is an invalid ABI type.
        """
        # simplest types to match against since they don't require regex magic
        match typestr:
            case "address":
                return datatypes.Address()
            case "bool":
                return datatypes.Bool()
            case "bytes":
                return datatypes.Bytes(-1)  # -1 denotes dynamic size
            case "string":
                return datatypes.String()

        # using fullmatch method to correctly match against the entire string
        if (mo := cls.VALUE_PATTERN.fullmatch(typestr)) is not None:
            # identify which type was matched, and validate it
            match mo.lastindex:
                case 1:  # bytes
                    if (size := int(mo[1])) not in range(1, 33):
                        raise ParseError(typestr, f"'{size}' is not a valid byte array width")
                    return datatypes.Bytes(size)
                case 3:  # fixed
                    if (size := int(mo[2])) not in range(8, 264, 8):
                        raise ParseError(typestr, f"'{size}' is not a valid fixed point width")
                    elif (precision := int(mo[3])) not in range(81):
                        raise ParseError(
                            typestr, f"'{precision}' is not a valid fixed point precision"
                        )
                    return datatypes.Fixed(size, precision, typestr[0] != "u")
                case 4:  # integer
                    if (size := int(mo[4])) not in range(8, 264, 8):
                        raise ParseError(typestr, f"'{size}' is not a valid integer width")
                    return datatypes.Integer(size, typestr[0] != "u")

        # array
        if (mo := cls.ARRAY_PATTERN.fullmatch(typestr)) is not None:
            subtype, size = mo[1], int(mo[2] or -1)  # if mo[2] is None the array is dynamic
            if size == 0:
                raise ParseError(typestr, "'0' is not a valid array size")
            # recurse and parse the subtype of the array
            return datatypes.Array(cls.parse(subtype), size)

        # tuple
        if cls.TUPLE_PATTERN.fullmatch(typestr) is not None:
            # goal: split the type string on commas while preserving any component tuples
            components, compstr = [], typestr[1:-1]
            depth, lastpos = 0, 0  # keep track of nested tuples
            for mo in re.finditer(r"\(|\)|,", compstr):
                match mo[0]:
                    case "(":  # tuple start
                        depth += 1
                    case ")":  # tuple end
                        depth -= 1
                    case "," if depth == 0:  # component separator
                        # append the component substring from lastpos up to the comma
                        components.append(compstr[lastpos : mo.start()])
                        lastpos = mo.end()  # set lastpos after the comma

            # append the remaining component after the last comma
            components.append(compstr[lastpos:])
            # validate we have no empty components (dangling commas)
            if "" in components:
                raise ParseError(typestr, "Dangling comma detected in type string")

            # recurse and parse components
            return datatypes.Tuple([cls.parse(component) for component in components])

        # none of the above matching was successful, raise since we can't parse `typestr`
        raise ParseError(typestr, "ABI type not parseable")
