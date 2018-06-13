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

from datetime import datetime

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
