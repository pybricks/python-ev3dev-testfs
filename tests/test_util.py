import time

from ev3dev.testfs._util import encode_dict, decode_dict, wait_for_mount


def test_encode_decode():
    SMALL_DICT = {'key': 'value'}
    enc = encode_dict(SMALL_DICT)
    assert type(enc) is str
    dec = decode_dict(enc)
    assert dec == SMALL_DICT


def test_wait_for_mount_timeout():
    TIMEOUT = 0.25
    timeout_error = False
    start_time = time.monotonic()
    try:
        wait_for_mount('---------', timeout=TIMEOUT)
    except TimeoutError:
        timeout_error = True

    assert timeout_error
    assert time.monotonic() - start_time > TIMEOUT
