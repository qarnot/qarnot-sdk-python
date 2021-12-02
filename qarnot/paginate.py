from typing import List, Any


class PaginateResponse:
    """A paginate response

    :param is_truncated: Is the object truncated
    :type is_truncated: `bool`
    :param token: the token to used to retrieve the page, defaults to None
    :type token: `str`
    :param next_token: the next page token to be used to continue the pagination, defaults to None
    :type next_token: `str`
    :param page_data: the data objects retrieved
    :type page_data: list of json `str` objects representation.
    """

    def __init__(self, token: str, next_token: str, is_truncated: bool, page_data: List[Any]):
        self.token = token
        self.next_token = next_token
        self.is_truncated = is_truncated
        self.page_data = page_data


class OffsetResponse:
    """An offseet response

    :param total: the total number of data objects
    :type total: `int`
    :param offset: the offset from which to display the response data, default to 0
    :type offset: `int`
    :param limit: the limit number of data objects to display
    :type limit: `int`
    :param page_data: the data objects retrieved
    :type page_data: list of json `str` objects representation.
    """

    def __init__(self, total: int, offset: int, limit: int, page_data: List[Any]):
        self.total = total
        self.offset = offset
        self.limit = limit
        self.page_data = page_data
