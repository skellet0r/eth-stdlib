import sha3


def keccak256(data: bytes) -> bytes:
    return sha3.keccak_256(data).digest()
