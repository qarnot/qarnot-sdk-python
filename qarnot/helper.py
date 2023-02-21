import logging
import sys
from typing import TextIO


DETAILED_LOG_FORMAT = ("%(asctime)s|%(process)d(%(processName)s):%(thread)d|%(name)s:%(filename)s:"
                       "%(lineno)s|%(funcName)s|%(levelname)s|%(message)s")

DEFAULT_LOG_FORMAT = "%(asctime)s|%(levelname)s|%(message)s"


class Log():
    """Helper to create logger that can be injected into connection and compute objects.
    """

    @staticmethod
    def get_logger_for_stream(stream: TextIO = None, log_format: str = DEFAULT_LOG_FORMAT):
        """Create a logger whose output is a stream.

        :param TextIO stream:
          (optional) the stream used to write the logs.
          Default is sys.stdout.
        :param str log_format:
          (optional) a custom format used for the logs.
          Default is "%(asctime)s|%(levelname)s|%(message)s"
          For more detailed log, DETAILED_LOG_FORMAT can be used:
            "%(asctime)s|%(process)d(%(processName)s):%(thread)d|%(name)s:%(filename)s:"
            "%(lineno)s|%(funcName)s|%(levelname)s|%(message)s"
          Other custom format can be used.

        :rtype: logging.Logger
        :returns: The created logger.
        """

        formatter = logging.Formatter(log_format)
        handler = logging.StreamHandler(stream if stream is not None else sys.stdout)
        handler.setFormatter(formatter)

        logger = logging.getLogger(__name__)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
