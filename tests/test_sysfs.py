import os
import sys
import time

from contextlib import contextmanager
from subprocess import Popen, PIPE
from tempfile import mkdtemp

from ev3dev.testfs import _sysfs


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
    p = Popen(args, stdin=PIPE, stdout=PIPE)
    try:
        wait_for_mount(mount_point)
        yield p
    finally:
        p.terminate()
        p.wait()


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


def test_ls_root():
    with get_tmp_dir() as t:
        with get_proc(t) as p:
            ls = os.listdir(t)
            assert 'class' in ls
            assert len(ls) == 1
