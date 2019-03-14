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
    time.sleep(1)  # FIXME: how to wait for mount?
    try:
        yield p
    finally:
        p.terminate()
        p.wait()


def test_ls_root():
    with get_tmp_dir() as t:
        with get_proc(t) as p:
            ls = os.listdir(t)
            assert 'class' in ls
            assert len(ls) == 1
