import fuse

from errno import ENOENT
from stat import S_IFDIR

fuse.fuse_python_api = (0, 2)

_CLASS_PATH = '/class'


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

    def getattr(self, path):
        st = SysfsStat()
        if path == '/':
            st.st_mode = S_IFDIR | 0o555
        elif path == _CLASS_PATH:
            st.st_mode = S_IFDIR | 0o755
        else:
            return -ENOENT
        return st

    def readdir(self, path, offset):
        for r in '.', '..', _CLASS_PATH[1:]:
            yield fuse.Direntry(r)

if __name__ == '__main__':
    f = SysfsFuse()
    f.parse()
    f.main()
