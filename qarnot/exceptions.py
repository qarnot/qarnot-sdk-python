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
           'BucketStorageUnavailableException',
           'UnauthorizedException',
           'MissingTaskException',
           'MissingPoolException',
           'MaxTaskException',
           'MaxPoolException',
           'NotEnoughCreditsException',
           'MissingBucketException',
           'MaxJobException',
           'MissingJobException']


class QarnotException(Exception):
    """Qarnot Exception"""
    pass


class QarnotGenericException(QarnotException):
    """General Connection exception"""
    def __init__(self, msg):
        super(QarnotGenericException, self).__init__("Error: {0}".format(msg))


class BucketStorageUnavailableException(QarnotException):
    """API bucket storage is disabled."""
    pass


class UnauthorizedException(QarnotException):
    """Invalid token."""
    pass


class MissingTaskException(QarnotException):
    """Non existent task."""
    pass


class MissingBucketException(QarnotException):
    """Non existent bucket."""
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


class NotEnoughCreditsException(QarnotException):
    """Not enough credits exception."""
    pass


class MissingJobException(Exception):
    """Non existentjob."""
    pass


class MaxJobException(Exception):
    """Max number of jobs reached."""
    pass
