import copy
import errno
import os
import stat
import sys
import time

from contextlib import contextmanager
from subprocess import Popen, PIPE
from tempfile import mkdtemp

import pytest

from ev3dev.testfs import _sysfs

ALL_BYTES = bytes((x for x in range(256)))

TEST_ROOT = {
    'name': '/',
    'type': 'directory',
    'mode': 0o755,
    'contents': [
        {
            'name': 'dir1',
            'type': 'directory',
            'mode': 0o755,
            'contents': [
                {
                    'name': 'dir2',
                    'type': 'directory',
                    'mode': 0o755,
                    'contents': [],
                }
            ],
        },
        {
            'name': 'file1',
            'type': 'file',
            'mode': 0o644,
            'contents': _sysfs.encode_bytes(ALL_BYTES),
        },
    ],
}


@contextmanager
def get_tmp_dir() -> str:
    t = mkdtemp()
    try:
        yield t
    finally:
        os.rmdir(t)


def wait_for_mount(mount_point: str, timeout: float = 0.5):
    """Wait for the mount point to appear.

    Parameters
    ----------
        mount_point
            The absolute path to the mount point.
        timeout
            Timeout in seconds

    Raises
    ------
        TimeoutError
            If the `timeout` is reached before the mount point is seen.
    """
    DELAY = 0.01  # delay in seconds between checks
    MAX_COUNT = timeout // DELAY
    count = 0
    while True:
        with open('/proc/mounts', 'r') as f:
            for line in f.readlines():
                if not line:
                    break
                if line.find(mount_point) > -1:
                    return
            if count > MAX_COUNT:
                raise TimeoutError('Waiting for mount took too long')
            count += 1
            time.sleep(DELAY)


@contextmanager
def get_proc(mount_point: str) -> Popen:
    args = [
        sys.executable, '-m', 'ev3dev.testfs._sysfs',
        mount_point,
        # '-d',
        '-f',
        '-o', 'auto_unmount'
    ]
    p = Popen(args, stdin=PIPE, stdout=PIPE, universal_newlines=True)
    try:
        wait_for_mount(mount_point)
        yield p
    finally:
        p.terminate()
        p.wait()


def test_encode_decode():
    SMALL_DICT = {'key': 'value'}
    enc = _sysfs.encode(SMALL_DICT)
    assert type(enc) is str
    dec = _sysfs.decode(enc)
    assert dec == SMALL_DICT


def test_encode_decode_bytes():
    enc = _sysfs.encode_bytes(ALL_BYTES)
    assert type(enc) is str
    dec = _sysfs.decode_bytes(enc)
    assert dec == ALL_BYTES


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


def test_parse_line():
    SMALL_DICT = {'key': 'value'}
    sysfs = _sysfs.SysfsFuse()

    sysfs._root = copy.deepcopy(SMALL_DICT)
    reply = sysfs._parse_line("GET")
    assert reply.split() == ['OK', 'eyJrZXkiOiAidmFsdWUifQ==']

    sysfs._root = copy.deepcopy(TEST_ROOT)
    reply = sysfs._parse_line("SET eyJrZXkiOiAidmFsdWUifQ==")
    assert reply.split() == ['OK']
    assert sysfs._root == SMALL_DICT


def test_get_item():
    sysfs = _sysfs.SysfsFuse()
    sysfs._root = dict(TEST_ROOT)

    item = sysfs._get_item('/')
    assert item['name'] == '/'

    item = sysfs._get_item('/dir1')
    assert item['name'] == 'dir1'

    item = sysfs._get_item('/dir1/dir2')
    assert item['name'] == 'dir2'

    item = sysfs._get_item('/dir1/dir2/dir3')
    assert item is None


def test_getattr():
    sysfs = _sysfs.SysfsFuse()
    sysfs._root = copy.deepcopy(TEST_ROOT)

    attr = sysfs.getattr('/')
    assert stat.S_IFMT(attr.st_mode) == stat.S_IFDIR
    assert stat.S_IMODE(attr.st_mode) == 0o755

    attr = sysfs.getattr('/dir1')
    assert stat.S_IFMT(attr.st_mode) == stat.S_IFDIR
    assert stat.S_IMODE(attr.st_mode) == 0o755

    attr = sysfs.getattr('/file1')
    assert stat.S_IFMT(attr.st_mode) == stat.S_IFREG
    assert stat.S_IMODE(attr.st_mode) == 0o644


def test_readdir():
    sysfs = _sysfs.SysfsFuse()
    sysfs._root = copy.deepcopy(TEST_ROOT)

    names = [x.name for x in sysfs.readdir('/', 0)]
    assert '.' in names
    assert '..' in names
    assert 'dir1' in names
    assert 'file1' in names
    assert len(names) == 4

    names = [x.name for x in sysfs.readdir('/dir1', 0)]
    assert '.' in names
    assert '..' in names
    assert 'dir2' in names
    assert len(names) == 3


def test_open():
    sysfs = _sysfs.SysfsFuse()
    sysfs._root = copy.deepcopy(TEST_ROOT)

    assert sysfs._root['contents'][1]['name'] == 'file1'

    # read/write file can be opened any which way
    sysfs._root['contents'][1]['mode'] = 0o666
    err = sysfs.open('/file1', os.O_RDONLY)
    assert err is None
    err = sysfs.open('/file1', os.O_WRONLY)
    assert err is None
    err = sysfs.open('/file1', os.O_RDWR)
    assert err is None

    # read-only file can only be opened for reading
    sysfs._root['contents'][1]['mode'] = 0o444
    err = sysfs.open('/file1', os.O_RDONLY)
    assert err is None
    err = sysfs.open('/file1', os.O_WRONLY)
    assert err == -errno.EACCES
    err = sysfs.open('/file1', os.O_RDWR)
    assert err == -errno.EACCES

    # write-only file can only be opened for writing
    sysfs._root['contents'][1]['mode'] = 0o222
    err = sysfs.open('/file1', os.O_RDONLY)
    assert err == -errno.EACCES
    err = sysfs.open('/file1', os.O_WRONLY)
    assert err is None
    err = sysfs.open('/file1', os.O_RDWR)
    assert err == -errno.EACCES


###############################################################################
# The tests below actually setup a FUSE mount and call _sysfs as a subprocess
###############################################################################


def test_stat_dir1():
    with get_tmp_dir() as t:
        with get_proc(t) as p:
            reply = p.stdout.readline().strip()
            assert reply == 'READY'

            msg = 'SET {}'.format(_sysfs.encode(TEST_ROOT))
            print(msg, file=p.stdin, flush=True)
            reply = p.stdout.readline().strip()
            assert reply == 'OK'

            st = os.stat(os.path.join(t, 'dir1'))
            assert stat.S_IFMT(st.st_mode) == stat.S_IFDIR
            assert stat.S_IMODE(st.st_mode) == 0o755


def test_ls_root():
    with get_tmp_dir() as t:
        with get_proc(t) as p:
            ls = os.listdir(t)
            assert len(ls) == 0


def test_ls_dir1():
    with get_tmp_dir() as t:
        with get_proc(t) as p:
            reply = p.stdout.readline().strip()
            assert reply == 'READY'

            msg = 'SET {}'.format(_sysfs.encode(TEST_ROOT))
            print(msg, file=p.stdin, flush=True)
            reply = p.stdout.readline().strip()
            assert reply == 'OK'

            ls = os.listdir(os.path.join(t, 'dir1'))
            assert 'dir2' in ls
            assert len(ls) == 1


def test_open_dir1():
    with get_tmp_dir() as t:
        with get_proc(t) as p:
            reply = p.stdout.readline().strip()
            assert reply == 'READY'

            msg = 'SET {}'.format(_sysfs.encode(TEST_ROOT))
            print(msg, file=p.stdin, flush=True)
            reply = p.stdout.readline().strip()
            assert reply == 'OK'

            with pytest.raises(OSError) as exc_info:
                with open(os.path.join(t, 'dir1')) as f:
                    pass
            assert exc_info.value.errno == errno.EISDIR


def test_open_file1():
    with get_tmp_dir() as t:
        with get_proc(t) as p:
            reply = p.stdout.readline().strip()
            assert reply == 'READY'

            msg = 'SET {}'.format(_sysfs.encode(TEST_ROOT))
            print(msg, file=p.stdin, flush=True)
            reply = p.stdout.readline().strip()
            assert reply == 'OK'

            with open(os.path.join(t, 'file1'), 'r') as f:
                pass

            with pytest.raises(OSError) as exc_info:
                with open(os.path.join(t, 'file1'), 'r+') as f:
                    pass
            assert exc_info.value.errno == errno.EACCES

            with pytest.raises(OSError) as exc_info:
                with open(os.path.join(t, 'file1'), 'w') as f:
                    pass
            assert exc_info.value.errno == errno.EACCES
