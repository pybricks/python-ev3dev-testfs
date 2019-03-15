import base64
import json
import time


def encode_dict(obj: dict) -> str:
    """Encode a dictionary to a base64 encoded json string."""
    dumps = json.dumps(obj, separators=(',', ':'))
    return base64.b64encode(dumps.encode()).decode()


def decode_dict(obj: str) -> dict:
    """Decode a base64 encoded json string to a dictionary."""
    return json.loads(base64.b64decode(obj.encode()))


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
