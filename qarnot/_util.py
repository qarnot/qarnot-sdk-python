# Copyright 2017 Qarnot computing
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime, timedelta
from requests import Response
from simplejson import JSONDecodeError as simpleJsonDecodeError
from json import JSONDecodeError
from http.client import responses

import re

_IS_PY2 = bytes is str

if not _IS_PY2:
    unicode = str


def copy_docs(docs_source):
    def decorator(obj):
        obj.__doc__ = docs_source.__doc__
        return obj
    return decorator


def decode(string, encoding='utf-8'):
    """Decode string if it is a bytes instance."""
    if isinstance(string, bytes):
        return string.decode(encoding)

    return string


def is_string(x):
    """Check if x is a string (bytes or unicode)."""
    return isinstance(x, (str, unicode))


def parse_to_timespan_string(value):
    """parse the value and return a timespan string

    :param value: Value to be parse
    :type value: :class:`str` or :class:`timedelta`
    :raises TypeError: The value can't be transform to a valid timespan, wrong type or wrong format
    :return: the valid timespan parsed
    :rtype: :class:`str`
    """
    if isinstance(value, str) and re.match(r'([0-9]\.)?[0-9]{2}:[0-9]{2}:[0-9]{2}', value):
        return value
    elif isinstance(value, timedelta):
        return convert_timedelta_to_timespan_string(value)
    raise TypeError("value must be a timedelta or time span format string (example: ``d.hh:mm:ss`` or ``hh:mm:ss`` )")


def convert_timedelta_to_timespan_string(duration):
    """Convert a timedelta python object to a timespan C sharp foramt string"""
    days, seconds = duration.days, duration.seconds
    hours = (seconds // 3600) % 24
    minutes = (seconds // 60) % 60
    seconds = seconds % 60
    return "{}.{:02d}:{:02d}:{:02d}".format(days, hours, minutes, seconds)


def parse_datetime(string):
    """Support multiple formats to parse a datetime"""
    try:
        # '2018-06-13T09:06:20Z'
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        # '2018-06-13T09:06:20.537708Z'
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")


def parse_timedelta(string):
    # """Support multiple formats to parse a datetime"""
    # [d'.']hh':'mm':'ss['.'fffffff].
    day, hour, minute, second, millisecond = 0, 0, 0, 0, 0
    day_string = '0'
    hour_string = '0'
    minute_string = '0'
    second_string = '0'
    millisecond_string = '0'
    if string is None:
        return timedelta(day, second, 0, millisecond, minute, hour)

    splitted_timedelta = string.split(":")
    if len(splitted_timedelta) == 3:
        # handle days and hours
        if ('.' in splitted_timedelta[0]):
            day_string, hour_string = splitted_timedelta[0].split('.')
        else:
            hour_string = splitted_timedelta[0]
        # handle minute
        minute_string = splitted_timedelta[1]
        # handle seconds and milliseconds
        if ('.' in splitted_timedelta[2]):
            second_string, millisecond_string = splitted_timedelta[2].split('.')
        else:
            second_string = splitted_timedelta[2]

        day = int(day_string)
        hour = int(hour_string)
        minute = int(minute_string)
        second = int(second_string)
        millisecond = int(millisecond_string)
    else:
        raise ValueError("parse_timedelta format should be [d'.']hh':'mm':'ss['.'fffffff].")

    return timedelta(day, second, 0, millisecond, minute, hour)


def get_sanitized_bucket_path(path: str, show_warning: bool = True):
    if path is not None:
        original_path = path
        warning = ""
        directory_separators = ['/', '\\']
        for separator in directory_separators:
            double_separator = separator + separator
            while path.__contains__(double_separator):
                warning = "Warning: Bucket path should not contain duplicated slashes (" + double_separator + ")\n"
                path = path.replace(double_separator, separator)
            if path.startswith(separator):
                warning += "Warning: Bucket path should not start with a slash (" + separator + ")\n"
                path = path.lstrip(separator)
        if path != original_path:
            warning += "Path changed from " + original_path + " to " + path + "\n"
            warning += "If bucket path sanitization is not wanted, please open a new connection with the constructor flag 'sanitize_bucket_paths=False'"
        if show_warning and warning != "":
            print(warning)
        return path.strip()
    return path


def get_error_message_from_http_response(response: Response, message_is_status_code_if_null: bool = False) -> str:
    error_message = ""
    try:
        error_response = response.json()
        if 'message' in error_response:
            error_message = error_response['message']
        elif 'error' in error_response:
            error_message = error_response['error']
    except (JSONDecodeError, simpleJsonDecodeError):
        error_message = response.text
    if (error_message is None or error_message == "" or len(error_message) < 1) and message_is_status_code_if_null:
        return responses[response.status_code]
    return error_message
