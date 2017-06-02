"""Exceptions."""


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


__all__ = ['QarnotException',
           'QarnotGenericException',
           'UnauthorizedException',
           'MissingTaskException',
           'MissingPoolException',
           'MaxTaskException',
           'MaxPoolException',
           'MissingDiskException',
           'MaxDiskException',
           'NotEnoughCreditsException',
           'LockedDiskException']


class QarnotException(Exception):
    """Qarnot Exception"""
    pass


class QarnotGenericException(QarnotException):
    """General Connection exception"""
    def __init__(self, msg):
        super(QarnotGenericException, self).__init__("Error: {0}".format(msg))


class UnauthorizedException(QarnotException):
    """Invalid token."""
    pass


class MissingTaskException(QarnotException):
    """Non existent task."""
    pass


class MissingPoolException(QarnotException):
    """Non existent pool."""
    pass


class MaxTaskException(QarnotException):
    """Max number of tasks reached."""
    pass


class MaxPoolException(QarnotException):
    """Max number of pools reached."""
    pass


class MissingDiskException(QarnotException):
    """Non existing disk."""
    pass


class MaxDiskException(QarnotException):
    """Max number of disks reached."""
    pass


class NotEnoughCreditsException(QarnotException):
    """Not enough credits exceptions."""
    pass


class LockedDiskException(QarnotException):
    """Locked disk."""
    pass
