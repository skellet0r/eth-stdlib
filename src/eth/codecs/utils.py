import functools
import string

from sha3 import keccak_256 as keccak256


@functools.singledispatch
def checksum_encode(addr: str | bytes) -> str:
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
    raise TypeError(
        f"Invalid argument type, expected 'str' or 'bytes' got: {type(addr).__qualname__}"
    )


@checksum_encode.register
def _(addr: str) -> str:
    if len(hexval := addr.lower().removeprefix("0x")) != 40:
        raise ValueError("Invalid value length")
    elif not set(hexval) < set(string.hexdigits):
        raise ValueError("Invalid hexadecimal characters")

    buffer = ""
    digest = keccak256(hexval.encode()).hexdigest()
    for char, nibble in zip(hexval, digest):
        buffer += char.upper() if int(nibble, 16) > 7 else char

    return "0x" + buffer


@checksum_encode.register
def _(addr: bytes) -> str:
    return checksum_encode(addr.hex())
