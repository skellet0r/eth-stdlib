from ethlib.codecs.abi import datatypes


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
