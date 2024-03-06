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
           'MissingProfileException',
           'MissingTaskInstanceException',
           'MissingTaskException',
           'MissingPoolInstanceException',
           'MissingPoolException',
           'MaxTaskException',
           'MaxPoolException',
           'NotEnoughCreditsException',
           'MissingBucketException',
           'MaxJobException',
           'MissingJobException',
           'SecretNotFoundException',
           'SecretConflictException']


class QarnotException(Exception):
    """Qarnot Exception"""


class QarnotGenericException(QarnotException):
    """General Connection exception"""
    def __init__(self, msg):
        super(QarnotGenericException, self).__init__("Error: {0}".format(msg))


class BucketStorageUnavailableException(QarnotException):
    """API bucket storage is disabled."""


class UnauthorizedException(QarnotException):
    """Invalid token."""


class MissingProfileException(QarnotException):
    """Non existent profile."""


class MissingTaskInstanceException(QarnotException):
    """Non existent instance for task."""


class MissingTaskException(QarnotException):
    """Non existent task."""


class MissingBucketException(QarnotException):
    """Non existent bucket."""


class MissingPoolInstanceException(QarnotException):
    """Non existent instance for pool."""


class MissingPoolException(QarnotException):
    """Non existent pool."""


class MaxTaskException(QarnotException):
    """Max number of tasks reached."""


class MaxPoolException(QarnotException):
    """Max number of pools reached."""


class NotEnoughCreditsException(QarnotException):
    """Not enough credits exception."""


class MissingJobException(Exception):
    """Non existent job."""


class MaxJobException(Exception):
    """Max number of jobs reached."""


class SecretNotFoundException(Exception):
    """Requested secret was not found."""


class SecretConflictException(Exception):
    """Secret already exists."""
