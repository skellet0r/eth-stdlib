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

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Literal


class DataType:
    """ABI data type base class.

    Note:
        Visitor classes should implement the appropriate 'visit_{ClassName}' methods.
    """

    def accept(self, visitor: object, *args, **kwargs) -> Any:
        """Accept a visitor and call the appropriate visit method on it.

        Returns:
            The output of the visit method on the visitor.

        Raises:
            AttributeError: If visitor does not have the appropriate visit method required defined.
        """
        fn = getattr(visitor, f"visit_{self.__class__.__name__}")
        return fn(self, *args, **kwargs)

    @cached_property
    def is_dynamic(self) -> bool:
        """Indicates if the data type instance is considered dynamic."""
        return False


@dataclass(init=False, eq=False, slots=True)
class Address(DataType):
    """Address Data Type."""


@dataclass(eq=False, slots=True)
class Array(DataType):
    """Array Data Type.

    Attributes:
        subtype: The data type of array elements.
        size: The size of the array. -1 if the array is dynamically sized.
    """

    subtype: DataType
    size: int

    @cached_property
    def is_dynamic(self) -> bool:
        return self.size == -1 or self.subtype.is_dynamic


@dataclass(init=False, eq=False, slots=True)
class Bool(DataType):
    """Boolean Data Type."""


@dataclass(eq=False, slots=True)
class Bytes(DataType):
    """Byte Array Data Type.

    Attributes:
        size: The size of the byte array. -1 if the byte array is dynamically sized.
    """

    size: int

    @cached_property
    def is_dynamic(self) -> bool:
        return self.size == -1


@dataclass(eq=False, slots=True)
class Fixed(DataType):
    """Fixed-Point Decimal Data Type.

    Attributes:
        size: The number of bits utilized by the data type.
        precision: The number of decimal points available.
        is_signed: True if the data type is signed, False otherwise.
    """

    size: int
    precision: int
    is_signed: bool


@dataclass(eq=False, slots=True)
class Integer(DataType):
    """Integer Data Type.

    Attributes:
        size: The number of bits utilized by the data type.
        is_signed: True if the data type is signed, False otherwise.
    """

    size: int
    is_signed: bool


@dataclass(init=False, eq=False, slots=True)
class String(DataType):
    """String Data Type."""

    @cached_property
    def is_dynamic(self) -> Literal[True]:
        return True


@dataclass(eq=False, slots=True)
class Tuple(DataType):
    """Tuple Data Type.

    Attributes:
        components: Ordered sequence of data types which the tuple is composed of.
    """

    components: list[DataType]

    @cached_property
    def is_dynamic(self):
        return any((elem.is_dynamic for elem in self.components))
