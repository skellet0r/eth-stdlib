import string

from eth.hash import keccak256


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
    if isinstance(addr, bytes):
        hexval = addr.hex()
    elif isinstance(addr, str):
        hexval = addr.lower().removeprefix("0x")
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
