import base64
import itertools
import json
import os
import sys
import threading

import fuse

from errno import ENOENT
from stat import S_IFDIR, S_IFREG

fuse.fuse_python_api = (0, 2)

_CLASS_PATH = '/class'

_ROOT = {
    'type': 'directory',
    'name': '/',
    'mode': 0o555,
    'contents': [
        {
            'type': 'directory',
            'name': 'class',
            'mode': 0o755,
            'contents': [
                {
                    'type': 'directory',
                    'name': 'lego-port',
                    'mode': 0o755,
                    'contents': [],
                },
                {
                    'type': 'directory',
                    'name': 'lego-sensor',
                    'mode': 0o755,
                    'contents': [],
                },
                {
                    'type': 'directory',
                    'name': 'tacho-motor',
                    'mode': 0o755,
                    'contents': [],
                },
            ],
        },
    ],
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
                data = base64.b64encode(json.dumps(self._root).encode())
                return 'OK {}'.format(data.decode())
            if line[0] == 'SET':
                self._root = json.loads(base64.b64decode(line[1]))
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
        st.st_mode |= item['mode']
        return st

    def readdir(self, path, offset):
        item = self._get_item(path)
        names = (x['name'] for x in item['contents'])
        for r in itertools.chain(['.', '..'], names):
            yield fuse.Direntry(r)

if __name__ == '__main__':
    f = SysfsFuse()
    f.parse()
    f.main()
