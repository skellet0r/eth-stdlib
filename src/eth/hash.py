import sha3


def keccak256(data: bytes) -> bytes:
    """Ethereum keccak256 hash function.

    Parameters:
        data: The data to hash.

    Returns:
        The hash digest.
    """
    return sha3.keccak_256(data).digest()
