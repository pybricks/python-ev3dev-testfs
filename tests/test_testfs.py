import errno
import os
import stat

from contextlib import contextmanager
from tempfile import mkdtemp

import pytest

from ev3dev.testfs import encode_bytes, decode_bytes, Sysfs


ALL_BYTES = bytes(range(256))

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
            'contents': encode_bytes(ALL_BYTES),
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


def test_encode_decode_bytes():
    assert len(ALL_BYTES) == 256
    enc = encode_bytes(ALL_BYTES)
    assert type(enc) is str
    dec = decode_bytes(enc)
    assert dec == ALL_BYTES


def test_sysfs_private_read_timeout():
    with get_tmp_dir() as t:
        with Sysfs(t) as sysfs:
            with pytest.raises(TimeoutError) as exc_info:
                sysfs._read()
            assert exc_info.type == TimeoutError


def test_sysfs_stat_dir1():
    with get_tmp_dir() as t:
        with Sysfs(t) as sysfs:
            sysfs.tree = TEST_ROOT

            st = os.stat(os.path.join(t, 'dir1'))
            assert stat.S_IFMT(st.st_mode) == stat.S_IFDIR
            assert stat.S_IMODE(st.st_mode) == 0o755


def test_sysfs_ls_root():
    with get_tmp_dir() as t:
        with Sysfs(t):
            ls = os.listdir(t)
            assert len(ls) == 0


def test_sysfs_ls_dir1():
    with get_tmp_dir() as t:
        with Sysfs(t) as sysfs:
            sysfs.tree = TEST_ROOT

            ls = os.listdir(os.path.join(t, 'dir1'))
            assert 'dir2' in ls
            assert len(ls) == 1


def test_sysfs_open_dir1():
    with get_tmp_dir() as t:
        with Sysfs(t) as sysfs:
            sysfs.tree = TEST_ROOT

            with pytest.raises(OSError) as exc_info:
                with open(os.path.join(t, 'dir1')):
                    pass
            assert exc_info.value.errno == errno.EISDIR


def test_sysfs_open_file1():
    with get_tmp_dir() as t:
        with Sysfs(t) as sysfs:
            sysfs.tree = TEST_ROOT

            with open(os.path.join(t, 'file1'), 'r'):
                pass

            with pytest.raises(OSError) as exc_info:
                with open(os.path.join(t, 'file1'), 'r+'):
                    pass
            assert exc_info.value.errno == errno.EACCES

            with pytest.raises(OSError) as exc_info:
                with open(os.path.join(t, 'file1'), 'w'):
                    pass
            assert exc_info.value.errno == errno.EACCES


def test_sysfs_read_file1():
    with get_tmp_dir() as t:
        with Sysfs(t) as sysfs:
            sysfs.tree = TEST_ROOT

            with open(os.path.join(t, 'file1'), 'rb') as f:
                data = f.read()
                assert data == ALL_BYTES
