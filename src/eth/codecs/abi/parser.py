import re

from ethlib.codecs.abi import datatypes
from ethlib.codecs.abi.exceptions import ParseError


class Parser:

    ARRAY_PATTERN = re.compile(r"(.+)\[(\d*)\]")
    SPLIT_PATTERN = re.compile(r"(\(.+\)(?:\[\d*\])*)|,")
    TUPLE_PATTERN = re.compile(r"\(.+\)")
    VALUE_PATTERN = re.compile(r"bytes(\d+)|u?(?:fixed(\d+)x(\d+)|int(\d+))")

    @classmethod
    def parse(cls, typestr: str) -> datatypes.DataType:
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
