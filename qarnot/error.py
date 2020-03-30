import sys


class Error(object):
    """Api error

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.code = json['code']
        """:type: :class:`str`

        Error code."""

        self.message = json['message']
        """:type: :class:`str`

        Error message."""

        self.debug = json['debug']
        """:type: :class:`str`

        Optional extra debug information"""

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member
