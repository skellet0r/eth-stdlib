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

import decimal
import functools
from dataclasses import dataclass, field
from typing import Any


@dataclass(init=False, frozen=True)
class ABITypeNode:
    """Base class for ABI type nodes.

    Attributes:
        width: The number of bytes the encoded type occupies in the static data section.
        is_dynamic: Indicator denoting whether the type is dynamic or not.
    """

    width: int = field(default=32, init=False, repr=False)
    is_dynamic: bool = field(default=False, init=False, repr=False)

    def accept(self, visitor: object, *args: Any, **kwargs: Any) -> Any:
        """Accept a visitor.

        Parameters:
            visitor: An object with visit methods.
            *args: Variable length argument list passed to the visit method.
            **kwargs: Arbitrary keyword arguments passed to the visit method.
        """
        fn = getattr(visitor, f"visit_{self.__class__.__name__}")
        return fn(self, *args, **kwargs)


@dataclass(init=False, frozen=True)
class AddressNode(ABITypeNode):
    """Address ABI type node."""

    def __str__(self) -> str:
        return "address"


@dataclass(frozen=True)
class ArrayNode(ABITypeNode):
    """Array ABI type node.

    Parameters:
        etype: The element type of the array.
        length: The number of elements in the array or ``None`` if the array is dynamic.

    Attributes:
        etype: The element type of the array.
        length: The number of elements in the array or ``None`` if the array is dynamic.
    """

    etype: ABITypeNode
    length: int | None = None

    def __post_init__(self):
        if self.etype.is_dynamic or self.length is None:
            object.__setattr__(self, "is_dynamic", True)
        else:
            object.__setattr__(self, "width", self.etype.width * self.length)

    def __str__(self) -> str:
        suffix = "[]" if self.length is None else f"[{self.length}]"
        return str(self.etype) + suffix


@dataclass(init=False, frozen=True)
class BooleanNode(ABITypeNode):
    """Boolean ABI type node."""

    def __str__(self) -> str:
        return "bool"


@dataclass(frozen=True)
class BytesNode(ABITypeNode):
    """Bytes ABI type node.

    Parameters:
        size: The number of bytes the type utilizes, or ``None`` if the type does not have a fixed
            width.

    Attributes:
        size: The number of bytes the type utilizes, or ``None`` if the type does not have a fixed
            width.
    """

    size: int | None = None

    def __post_init__(self):
        object.__setattr__(self, "is_dynamic", self.size is None)

    def __str__(self) -> str:
        suffix = "" if self.size is None else f"{self.size}"
        return "bytes" + suffix


@dataclass(frozen=True)
class IntegerNode(ABITypeNode):
    """Integer ABI type node.

    Parameters:
        bits: The number of bits the type utilizes.
        is_signed: Indicator denoting whether the type is signed using two's complement.

    Attributes:
        bits: The number of bits the type utilizes.
        is_signed: Indicator denoting whether the type is signed using two's complement.
    """

    bits: int
    is_signed: bool = False

    @property
    def bounds(self) -> tuple[int, int]:
        """Get the lower and upper integer bounds of the type.

        Returns:
            A tuple with the lower and upper bounds of the type.
        """
        return self._calculate_bounds(self.bits, self.is_signed)

    @staticmethod
    @functools.cache
    def _calculate_bounds(bits: int, is_signed: bool = False) -> tuple[int, int]:
        """Calculate integer bounds.

        Parameters:
            bits: The number of bits the type utilizes.
            is_signed: Whether to calculate the bounds of a signed integer or not.

        Returns:
            A tuple with the calculated lower and upper bounds.
        """
        lo, hi = 0, 2**bits - 1
        if is_signed:
            lo -= 2 ** (bits - 1)
            hi += lo
        return lo, hi

    def __str__(self) -> str:
        prefix = "" if self.is_signed else "u"
        return prefix + f"int{self.bits}"


@dataclass(frozen=True)
class FixedNode(ABITypeNode):
    """Fixed point decimal ABI type node.

    Parameters:
        bits: The number of bits the type utilizes.
        precision: The number of decimal places the type utilizes.
        is_signed: Indicator denoting whether the type is signed using two's complement.

    Attributes:
        bits: The number of bits the type utilizes.
        precision: The number of decimal places the type utilizes.
        is_signed: Indicator denoting whether the type is signed using two's complement.
    """

    bits: int
    precision: int
    is_signed: bool = False

    @property
    def bounds(self) -> tuple[decimal.Decimal, decimal.Decimal]:
        """Get the lower and upper fixed point decimal bounds of the type.

        Returns:
            A tuple with the lower and upper bounds of the type.
        """
        return self._calculate_bounds(self.bits, self.precision, self.is_signed)

    @staticmethod
    @functools.cache
    def _calculate_bounds(
        bits: int, precision: int, is_signed: bool = False
    ) -> tuple[decimal.Decimal, decimal.Decimal]:
        """Calculate fixed point decimal bounds.

        Parameters:
            bits: The number of bits the type utilizes.
            precision: The number of decimal places the type utilizes.
            is_signed: Whether to calculate the bounds of a signed integer or not.

        Returns:
            A tuple with the calculated lower and upper bounds.
        """
        ilo, ihi = IntegerNode._calculate_bounds(bits, is_signed)
        with decimal.localcontext(decimal.Context(prec=80)):
            return decimal.Decimal(ilo).scaleb(-precision), decimal.Decimal(ihi).scaleb(-precision)

    def __str__(self) -> str:
        prefix = "" if self.is_signed else "u"
        return prefix + f"fixed{self.bits}x{self.precision}"


@dataclass(init=False, frozen=True)
class StringNode(ABITypeNode):
    """String ABI type node."""

    is_dynamic: bool = True

    def __str__(self) -> str:
        return "string"


@dataclass(frozen=True)
class TupleNode(ABITypeNode):
    """Tuple ABI type node.

    Parameters:
        ctypes: The component types of the tuple.

    Attributes:
        ctypes: The component types of the tuple.
    """

    ctypes: tuple[ABITypeNode, ...]

    def __post_init__(self):
        if any((typ.is_dynamic for typ in self.ctypes)):
            object.__setattr__(self, "is_dynamic", True)
        else:
            object.__setattr__(self, "width", sum((typ.width for typ in self.ctypes)))

    def __str__(self) -> str:
        inner = ",".join(map(str, self.ctypes))
        return f"({inner})"
