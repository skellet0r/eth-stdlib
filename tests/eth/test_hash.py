from eth.hash import keccak256


def test_correct_keccak256():
    keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
