
from ev3dev.testfs import encode_bytes, decode_bytes


ALL_BYTES = bytes(range(256))


def test_encode_decode_bytes():
    assert len(ALL_BYTES) == 256
    enc = encode_bytes(ALL_BYTES)
    assert type(enc) is str
    dec = decode_bytes(enc)
    assert dec == ALL_BYTES
