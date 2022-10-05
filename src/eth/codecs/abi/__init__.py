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

from typing import Any

from eth.codecs.abi.decoder import Decoder
from eth.codecs.abi.encoder import Encoder
from eth.codecs.abi.parser import Parser


def encode(schema: str, value: Any) -> bytes:
    """Encode a value according to an ABI schema.

    Parameters:
        schema: An ABI type string.
        value: The value to encode.

    Example:

        >>> encode("uint256", 42).hex()
        '000000000000000000000000000000000000000000000000000000000000002a'
        >>> encode("int128", -42).hex()
        'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd6'

    Returns:
        The encoded value.

    Raises:
        EncodeError: If value, or an element thereof, is not encodable.
        ParseError: If ``schema`` is an invalid ABI type.
    """
    return Encoder.encode(Parser.parse(schema), value)


def decode(schema: str, value: bytes, **kwargs) -> Any:
    """Decode a value according to an ABI schema.

    Parameters:
        schema: An ABI type string.
        value: The value to decode.
        **kwargs: Additional keyword arguments to pass on to ABI type decoder functions.

    Keyword Arguments:
        checksum (bool): Whether to checksum encode decoded address values, defaults to ``True``.

    Example:

        >>> decode("uint256", encode("uint256", 42))
        42
        >>> decode("int128", encode("int128", -42))
        -42

    Returns:
        The decoded value.

    Raises:
        DecodeError: If value, or an element thereof, is not decodable.
        ParseError: If ``schema`` is an invalid ABI type.
    """
    return Decoder.decode(Parser.parse(schema), value, **kwargs)
