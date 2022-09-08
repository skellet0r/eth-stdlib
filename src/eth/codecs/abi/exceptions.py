class ABIError(Exception):
    ...


class ParseError(ABIError):
    def __init__(self, where: str, msg: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.where = where
        self.msg = msg

    def __str__(self) -> str:
        return f"Error at {self.where!r} - {self.msg}"
