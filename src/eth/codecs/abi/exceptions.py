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
