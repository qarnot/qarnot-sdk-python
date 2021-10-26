import time
from .exceptions import UnauthorizedException


def with_retry(http_request_func):
    def _with_retry(self, *args, **kwargs):
        retry = self._retry_count
        last_chance = False

        while True:
            try:
                ret = http_request_func(self, *args, **kwargs)
            except ConnectionError:
                if last_chance:
                    raise

            if ret.ok:
                return ret
            if ret.status_code == 401:
                raise UnauthorizedException()
            # Do not retry on error except for rate limiting errors.
            if 400 <= ret.status_code <= 499 and ret.status_code != 429:
                return ret
            if last_chance:
                return ret

            if retry > 1:
                retry -= 1
                time.sleep(self._retry_wait * (self._retry_count - retry))
            else:
                last_chance = True

    return _with_retry
