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

import string
from typing import Union

from eth.hash import keccak256


def checksum_encode(addr: Union[str, bytes]) -> str:
    """Checksum encode an address.

    See `EIP-55 <https://eips.ethereum.org/EIPS/eip-55>`_.

    Parameters:
        addr: The address to checksum encode.

    Returns:
        The checksum encoded address.

    Raises:
        TypeError: If ``addr`` argument is not an instance of ``str`` or ``bytes``.
        ValueError: If ``addr`` contains non-hexadecimal characters or is not the proper length.
    """
    if isinstance(addr, bytes):
        hexval = addr.hex()
    elif isinstance(addr, str):
        addr = addr[2:] if addr[:2].lower() == "0x" else addr
        hexval = addr.lower()
    else:
        raise TypeError(
            f"Invalid argument type, expected 'str' or 'bytes' got: {type(addr).__qualname__}"
        )

    if len(hexval) != 40:
        raise ValueError("Invalid value length")
    elif not set(hexval) < set(string.hexdigits):
        raise ValueError("Invalid hexadecimal characters")

    buffer = ""
    digest = keccak256(hexval.encode()).hex()
    for char, nibble in zip(hexval, digest):
        buffer += char.upper() if int(nibble, 16) > 7 else char

    return "0x" + buffer
