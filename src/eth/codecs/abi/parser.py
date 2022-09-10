"""This file is part of eth-stdlib.
Copyright (C) 2022  Edward Amor

eth-stdlib is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

eth-stdlib is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import re

from eth.codecs.abi import datatypes
from eth.codecs.abi.exceptions import ParseError


class Parser:
    """Ethereum ABI type string parser.

    Attributes:
        ARRAY_PATTERN: compiled regex for matching array type strings.
        SPLIT_PATTERN: compiled regex for splitting tuple type strings on commas, while preserving
            component tuples entirely (if present).
        TUPLE_PATTERN: compiled regex for matching tuple type strings.
        VALUE_PATTERN: compiled regex for matching value type strings 'bytesN', 'uintN', 'intN',
            'ufixedMxN', and 'fixedMxN'.
    """

    ARRAY_PATTERN = re.compile(r"(.+)\[(\d*)\]")
    SPLIT_PATTERN = re.compile(r"(\(.+\)(?:\[\d*\])*)|,")
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
        match typestr:
            case "address":
                return datatypes.Address()
            case "bool":
                return datatypes.Bool()
            case "bytes":
                return datatypes.Bytes(-1)
            case "string":
                return datatypes.String()

        if (mo := cls.VALUE_PATTERN.fullmatch(typestr)) is not None:
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

        # tuple
        if cls.TUPLE_PATTERN.fullmatch(typestr) is not None:
            # split typestr on commas and tuples
            components = [cls.parse(typ) for typ in cls.SPLIT_PATTERN.split(typestr[1:-1]) if typ]
            return datatypes.Tuple(components)

        # array
        if (mo := cls.ARRAY_PATTERN.fullmatch(typestr)) is not None:
            # -1 denotes dynamic size
            subtype, size = mo[1], int(mo[2] or -1)
            if size == 0:
                raise ParseError(typestr, "'0' is not a valid array size")
            return datatypes.Array(cls.parse(subtype), size)

        raise ParseError(typestr, "ABI type not parseable")
