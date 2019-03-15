import base64

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def encode_bytes(b: bytes) -> str:
    """Encode a bytes-like object into a base64 unicode string object."""
    return base64.b64encode(b).decode()


def decode_bytes(s: str) -> bytes:
    """Decode a bytes-like object from a base64 unicode string object."""
    return base64.b64decode(s.encode())
