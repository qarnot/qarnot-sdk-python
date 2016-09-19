"""Exceptions."""


# Copyright 2016 Qarnot computing
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


__all__ = ['QarnotGenericException',
           'UnauthorizedException',
           'MissingTaskException',
           'MaxTaskException',
           'MissingDiskException',
           'MaxDiskException',
           'NotEnoughCreditsException',
           'LockedDiskException']


class QarnotGenericException(Exception):
    """General Connection exception"""
    def __init__(self, msg):
        super(QarnotGenericException, self).__init__("Error : {0}".format(msg))


class UnauthorizedException(Exception):
    """Authorization given is not valid."""
    def __init__(self, auth):
        super(UnauthorizedException, self).__init__(
            "invalid credentials : {0}".format(auth))


class MissingTaskException(Exception):
    """Non existent task."""
    def __init__(self, message, name):
        super(MissingTaskException, self).__init__(
            "{0}: {1}".format(message, name))


class MaxTaskException(Exception):
    """Max number of tasks reached."""
    pass


class MissingDiskException(Exception):
    """Non existing disk."""
    def __init__(self, message):
        super(MissingDiskException, self).__init__(message)


class MaxDiskException(Exception):
    """Max number of disks reached."""
    pass


class NotEnoughCreditsException(Exception):
    """Not enough credits exceptions."""
    pass


class LockedDiskException(Exception):
    """Locked disk."""
    def __init__(self, message):
        super(LockedDiskException, self).__init__(message)
