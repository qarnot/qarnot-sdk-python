import time
from .exceptions import UnauthorizedException


TRANSIENT_ERROR_CODES = [
    429,
    500,
    502,
    503,
    504,
]


def with_retry(http_request_func):
    def _with_retry(self, *args, **kwargs):
        tries = 0

        while True:
            try:
                ret = http_request_func(self, *args, **kwargs)
            except ConnectionError:
                if tries >= self._retry_count:
                    raise
                continue

            if ret.ok:
                return ret
            if ret.status_code == 401:
                raise UnauthorizedException()
            if ret.status_code not in TRANSIENT_ERROR_CODES:
                return ret

            if tries < self._retry_count:
                time.sleep((2 ** tries) * self._retry_wait)
                tries += 1
            else:
                return ret

    return _with_retry
