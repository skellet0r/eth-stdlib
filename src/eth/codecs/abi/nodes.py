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
from functools import cache, cached_property
from typing import Any, Literal


class Node:
    """ABI type node base class.

    Note:
        Visitor classes should implement the appropriate 'visit_{ClassName}' methods.
    """

    def accept(self, visitor: object, *args, **kwargs) -> Any:
        """Accept a visitor and call the appropriate visit method on it.

        Parameters:
            visitor: Object to call visit method on.
            *args: Additional positional arguments to pass to the visit function.
            **kwargs: Additional keyword arguments to pass to the visit function.

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

    def __len__(self) -> int:
        """Expected bytes the encoded element will occupy in the head of a tuple or array."""
        return 32


@dataclass(init=False, eq=False, slots=True)
class Address(Node):
    """Address Data Type."""


@dataclass(eq=False, slots=True)
class Array(Node):
    """Array Data Type.

    Parameters:
        subtype: The data type of array elements.
        size: The size of the array. -1 if the array is dynamically sized.

    Attributes:
        subtype: The data type of array elements.
        size: The size of the array. -1 if the array is dynamically sized.
    """

    subtype: Node
    size: int

    @cached_property
    def is_dynamic(self) -> bool:
        return self.size == -1 or self.subtype.is_dynamic

    @cache
    def __len__(self) -> int:
        if not self.is_dynamic:
            # 1) static array, w/ static elements
            # each element is concatenated so the total size of the array is the product of the
            # subtype's width * the number of elements in the array
            return len(self.subtype) * self.size
        else:
            # 2) dynamic array, w/ static elements - ptr
            # 3) static array, w/ dynamic elements - ptr
            # 4) dynamic array, w/ dynamic elements - ptr
            # all types which are dynamic or contain dynamic components get stored in the tail
            # and a pointer is placed in the head
            return 32


@dataclass(init=False, eq=False, slots=True)
class Bool(Node):
    """Boolean Data Type."""


@dataclass(eq=False, slots=True)
class Bytes(Node):
    """Byte Array Data Type.

    Parameters:
        size: The size of the byte array. -1 if the byte array is dynamically sized.

    Attributes:
        size: The size of the byte array. -1 if the byte array is dynamically sized.
    """

    size: int

    @cached_property
    def is_dynamic(self) -> bool:
        return self.size == -1


@dataclass(eq=False, slots=True)
class Fixed(Node):
    """Fixed-Point Decimal Data Type.

    Parameters:
        size: The number of bits utilized by the data type.
        precision: The number of decimal points available.
        is_signed: True if the data type is signed, False otherwise.

    Attributes:
        size: The number of bits utilized by the data type.
        precision: The number of decimal points available.
        is_signed: True if the data type is signed, False otherwise.
    """

    size: int
    precision: int
    is_signed: bool


@dataclass(eq=False, slots=True)
class Integer(Node):
    """Integer Data Type.

    Parameters:
        size: The number of bits utilized by the data type.
        is_signed: True if the data type is signed, False otherwise.

    Attributes:
        size: The number of bits utilized by the data type.
        is_signed: True if the data type is signed, False otherwise.
    """

    size: int
    is_signed: bool


@dataclass(init=False, eq=False, slots=True)
class String(Node):
    """String Data Type."""

    @cached_property
    def is_dynamic(self) -> Literal[True]:
        return True


@dataclass(eq=False, slots=True)
class Tuple(Node):
    """Tuple Data Type.

    Parameters:
        components: Ordered sequence of data types which the tuple is composed of.

    Attributes:
        components: Ordered sequence of data types which the tuple is composed of.
    """

    components: list[Node]

    @cached_property
    def is_dynamic(self):
        return any((elem.is_dynamic for elem in self.components))

    @cache
    def __len__(self) -> int:
        if not self.is_dynamic:
            # each element is concatenated and placed in the head
            return sum([len(elem) for elem in self.components])
        return 32
