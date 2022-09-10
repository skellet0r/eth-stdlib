from dataclasses import dataclass
from functools import cached_property
from typing import Any, Literal


class DataType:
    def accept(self, visitor: object, *args, **kwargs) -> Any:
        fn = getattr(visitor, f"visit_{self.__class__.__name__}")
        return fn(self, *args, **kwargs)

    @cached_property
    def is_dynamic(self) -> bool:
        return False


@dataclass(init=False, eq=False, slots=True)
class Address(DataType):
    ...


@dataclass(eq=False, slots=True)
class Array(DataType):
    subtype: DataType
    size: int

    @cached_property
    def is_dynamic(self) -> bool:
        return self.size == -1 or self.subtype.is_dynamic


@dataclass(init=False, eq=False, slots=True)
class Bool(DataType):
    ...


@dataclass(eq=False, slots=True)
class Bytes(DataType):
    size: int

    @cached_property
    def is_dynamic(self) -> bool:
        return self.size == -1


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
    @cached_property
    def is_dynamic(self) -> Literal[True]:
        return True


@dataclass(eq=False, slots=True)
class Tuple(DataType):
    components: list[DataType]

    @cached_property
    def is_dynamic(self):
        return any((elem.is_dynamic for elem in self.components))
