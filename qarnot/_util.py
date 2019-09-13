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


def parse_datetime(string):
    """Support multiple formats to parse a datetime"""
    try:
        # '2018-06-13T09:06:20Z'
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        pass

    try:
        # '2018-06-13T09:06:20.537708Z'
        return datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except Exception:
        raise


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

    try:
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
    except Exception:
        raise

    return timedelta(day, second, 0, millisecond, minute, hour)
