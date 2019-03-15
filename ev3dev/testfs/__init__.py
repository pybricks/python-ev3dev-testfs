import base64
import sys

from subprocess import Popen, PIPE

from ._util import encode_dict, decode_dict, wait_for_mount

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def encode_bytes(b: bytes) -> str:
    """Encode a bytes-like object into a base64 unicode string object."""
    return base64.b64encode(b).decode()


def decode_bytes(s: str) -> bytes:
    """Decode a bytes-like object from a base64 unicode string object."""
    return base64.b64decode(s.encode())


class Sysfs():
    """Class to manage a fake sysfs file system."""
    def __init__(self, mount_point: str):
        """
        Parameters
        ----------
        mount_point
            The absolute path to an existing directory where the filesystem
            will be mounted.
        """
        args = [
            sys.executable, '-m', 'ev3dev.testfs._sysfs',
            mount_point,
            # '-d',
            '-f',
            '-o', 'auto_unmount'
        ]
        self._mount_point = mount_point
        self._p = Popen(args, stdin=PIPE, stdout=PIPE, universal_newlines=True)

    def __enter__(self):
        if self._p.stdout.readline().strip() != 'READY':
            raise IOError('remote process is not ready')
        wait_for_mount(self._mount_point)
        return self

    def __exit__(self, *a):
        self._p.terminate()
        self._p.wait()

    @property
    def tree(self) -> dict:
        """Gets and sets a dictionary describing the filesystem structure."""
        msg = 'GET {}'.format(encode_dict(d))
        print(msg, file=self._p.stdin, flush=True)
        reply = self._p.stdout.readline().strip().split()
        if reply[0] != 'OK':
            # TODO: get error message from reply
            raise IOError()
        return decode_dict(reply[1])

    @tree.setter
    def tree(self, d: dict):
        msg = 'SET {}'.format(encode_dict(d))
        print(msg, file=self._p.stdin, flush=True)
        reply = self._p.stdout.readline().strip()
        if reply != 'OK':
            # TODO: get error message from reply
            raise IOError()
