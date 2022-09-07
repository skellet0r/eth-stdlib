from dataclasses import dataclass
from typing import Any


class DataType:
    def accept(self, visitor: object, *args, **kwargs) -> Any:
        fn = getattr(visitor, f"visit_{self.__class__.__name__}")
        return fn(self, *args, **kwargs)


@dataclass(init=False, eq=False, slots=True)
class Address(DataType):
    ...


@dataclass(eq=False, slots=True)
class Array(DataType):
    subtype: DataType
    size: int


@dataclass(init=False, eq=False, slots=True)
class Bool:
    ...


@dataclass(eq=False, slots=True)
class Bytes(DataType):
    size: int


@dataclass(eq=False, slots=True)
class Fixed(DataType):
    size: int
    precision: int
    is_signed: bool


@dataclass(eq=False, slots=True)
class Integer(DataType):
    size: int
    is_signed: bool


@dataclass(init=False, eq=False, slots=True)
class String(DataType):
    ...


@dataclass(eq=False, slots=True)
class Tuple(DataType):
    components: list[DataType]
