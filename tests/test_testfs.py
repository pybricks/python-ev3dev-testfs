import errno
import select
import stat

from pathlib import Path

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
        {
            'name': 'file2',
            'type': 'file',
            'mode': 0o666,
            'contents': '',
        },
    ],
}


def test_encode_decode_bytes():
    assert len(ALL_BYTES) == 256
    enc = encode_bytes(ALL_BYTES)
    assert type(enc) is str
    dec = decode_bytes(enc)
    assert dec == ALL_BYTES


def test_sysfs_private_read_timeout(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        with pytest.raises(TimeoutError) as exc_info:
            sysfs._read()
        assert exc_info.type == TimeoutError


def test_sysfs_stat_dir1(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        sysfs.tree = TEST_ROOT

        st = tmp_path.joinpath('dir1').stat()
        assert stat.S_IFMT(st.st_mode) == stat.S_IFDIR
        assert stat.S_IMODE(st.st_mode) == 0o755


def test_sysfs_ls_root(tmp_path: Path):
    with Sysfs(tmp_path):
        ls = list(tmp_path.iterdir())
        assert len(ls) == 0


def test_sysfs_ls_dir1(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        sysfs.tree = TEST_ROOT

        ls = [x.name for x in tmp_path.joinpath('dir1').iterdir()]
        assert 'dir2' in ls
        assert len(ls) == 1


def test_sysfs_open_dir1(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        sysfs.tree = TEST_ROOT

        with pytest.raises(OSError) as exc_info:
            with open(tmp_path.joinpath('dir1')):
                pass
        assert exc_info.value.errno == errno.EISDIR


def test_sysfs_open_file1(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        sysfs.tree = TEST_ROOT

        with open(tmp_path.joinpath('file1'), 'r'):
            pass

        with pytest.raises(OSError) as exc_info:
            with open(tmp_path.joinpath('file1'), 'r+'):
                pass
        assert exc_info.value.errno == errno.EACCES

        with pytest.raises(OSError) as exc_info:
            with open(tmp_path.joinpath('file1'), 'w'):
                pass
        assert exc_info.value.errno == errno.EACCES


def test_sysfs_read_file1(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        sysfs.tree = TEST_ROOT

        data = tmp_path.joinpath('file1').read_bytes()
        assert data == ALL_BYTES


def test_sysfs_write_file2(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        sysfs.tree = TEST_ROOT

        written = tmp_path.joinpath('file2').write_bytes(b'test')
        assert written == 4
        file2 = sysfs.tree['contents'][2]
        assert file2['name'] == 'file2'
        assert decode_bytes(file2['write_data']) == b'test'
        assert file2['write_offset'] == 0


def test_sysfs_poll_file1(tmp_path: Path):
    with Sysfs(tmp_path) as sysfs:
        sysfs.tree = TEST_ROOT

        with open(tmp_path.joinpath('file1'), 'rb') as f:
            p = select.poll()
            p.register(f.fileno(), select.POLLIN)

            # poll_events have not been set for file1, so poll() should
            # time out
            ok = True
            for fd, events in p.poll(500):
                ok = False
            assert ok  # didn't timed out if not ok

            sysfs.notify('/file1', select.POLLIN | select.POLLERR)

            # now we have sent a notification, so poll() should return
            # something
            ok = False
            for fd, events in p.poll(500):
                assert fd == f.fileno()
                assert events == select.POLLIN | select.POLLERR
                ok = True
            assert ok  # timed out if not ok
