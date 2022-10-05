import pytest

from eth.codecs.utils import checksum_encode


@pytest.mark.parametrize(
    "addr",
    [
        "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed",
        "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
        "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB",
        "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb",
    ],
)
def test_checksum_encode(addr):
    assert checksum_encode(addr) == addr
    assert checksum_encode(bytes.fromhex(addr[2:])) == addr


def test_checksum_encode_errors():
    with pytest.raises(TypeError, match="Invalid argument type, expected 'str' or 'bytes'"):
        checksum_encode({})

    for val in ["0x012133131132", (0).to_bytes(21, "big")]:
        with pytest.raises(ValueError, match="Invalid value length"):
            checksum_encode(val)

    with pytest.raises(ValueError, match="Invalid hexadecimal characters"):
        checksum_encode("0x" + "gg" * 20)
