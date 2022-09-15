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


def encode(typestr: str, value: Any) -> bytes:
    """Encode a value according to an ABI type string.

    Parameters:
        typestr: An ABI type string (i.e. 'uint256[]', '(uint8,bytes32)').
        value: The value to encode.

    Returns:
        The encoded value.

    Raises:
        EncodeError: if value, or an element thereof, is not encodable.
        ParseError: if `typestr`, or a sub-string thereof, is an invalid ABI type.
    """
    return Encoder.encode(Parser.parse(typestr), value)


def decode(typestr: str, value: bytes) -> Any:
    """Decode a value according to an ABI type string.

    Parameters:
        typestr: An ABI type string (i.e. 'uint256[]', '(uint8,bytes32)').
        value: The value to decode.

    Returns:
        The decoded value.

    Raises:
        DecodeError: if value, or an element thereof, is not decodable.
        ParseError: if `typestr`, or a sub-string thereof, is an invalid ABI type.
    """
    return Decoder.decode(Parser.parse(typestr), value)
