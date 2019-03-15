import itertools
import os
import threading

import fuse

from errno import EACCES, ENOENT, ENOTSUP
from stat import S_IFDIR, S_IFREG

from ..testfs import encode_bytes, decode_bytes
from ._util import encode_dict, decode_dict

fuse.fuse_python_api = (0, 2)

_ROOT = {
    'type': 'directory',
    'name': '/',
    'mode': 0o555,
    'contents': [],
}


class SysfsStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


class SysfsFuse(fuse.Fuse):
    def __init__(self):
        super().__init__()
        self._root = dict(_ROOT)
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True

    def _parse_line(self, line: str) -> str:
        try:
            line = line.split()
            if line[0] == 'GET':
                return 'OK {}'.format(encode_dict(self._root))
            if line[0] == 'SET':
                self._root = decode_dict(line[1])
                return 'OK'
            raise ValueError('Unknown command: {}'.format(line[0]))
        except Exception as ex:
            return 'ERR {}'.format(ex)

    def _run(self):
        print('READY', flush=True)
        while True:
            line = input()
            print(self._parse_line(line), flush=True)

    def _get_item(self, path: str) -> dict:
        current = None
        for n in path.split('/'):
            if n == '':
                if current:
                    # trailing '/'
                    continue
                # leading '/' means root node
                current = self._root
            else:
                # must be child of current directory
                if current['type'] != 'directory':
                    # path was not found
                    return None

                match = (x for x in current['contents'] if x['name'] == n)
                current = next(match, None)

            if not current:
                return None

        return current

    def main(self):
        self._thread.start()
        super().main()

    def getattr(self, path):
        item = self._get_item(path)
        if not item:
            return -ENOENT

        st = SysfsStat()
        if item['type'] == 'directory':
            st.st_mode |= S_IFDIR
        elif item['type'] == 'file':
            st.st_mode |= S_IFREG
            st.st_size = 4096  # all sysfs files are this size
        st.st_mode |= item['mode']
        return st

    def getxattr(self, path, name, size):
        return -ENOTSUP

    def setxattr(self, path, name, value, flags):
        return -ENOTSUP

    def readdir(self, path, offset):
        item = self._get_item(path)
        names = (x['name'] for x in item['contents'])
        for r in itertools.chain(['.', '..'], names):
            yield fuse.Direntry(r)

    def open(self, path, flags):
        item = self._get_item(path)
        if not item:
            return -ENOENT

        # Like real sysfs, the access mode must match the file permissions. To
        # make things easy, we are just looking at the group bits since that is
        # what matters in ev3dev.

        def match(accmode, mode_mask):
            return ((flags & os.O_ACCMODE) == accmode and
                    (item['mode'] & mode_mask) == mode_mask)

        if not (match(os.O_RDONLY, 0o040) or match(os.O_WRONLY, 0o020) or
                match(os.O_RDWR, 0o060)):
            return -EACCES

    def read(self, path, size, offset):
        item = self._get_item(path)
        if not item:
            return -ENOENT

        contents = decode_bytes(item['contents'])
        slen = len(contents)
        if offset < slen:
            if offset + size > slen:
                size = slen - offset
            buf = contents[offset:offset+size]
        else:
            buf = b''

        return buf

    def write(self, path, buf, offset):
        item = self._get_item(path)
        if not item:
            return -ENOENT

        item['written'] = {
            'buf': encode_bytes(buf),
            'offset': offset,
        }

        return len(buf)

    def truncate(self, path, size):
        item = self._get_item(path)
        if not item:
            return -ENOENT

        # truncate doesn't do anything in sysfs

    def flush(self, path):
        pass


if __name__ == '__main__':
    f = SysfsFuse()
    f.parse()
    f.main()
