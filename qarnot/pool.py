"""Module to handle a pool."""

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
import time
import warnings

import datetime

from . import raise_on_error, get_url
from .bucket import Bucket
from .disk import Disk
from .status import Status
from .exceptions import MissingPoolException, MaxDiskException, MaxPoolException, NotEnoughCreditsException, \
    MissingDiskException, LockedDiskException


class Pool(object):
    """Represents a Qarnot pool.

    .. note::
       A :class:`Pool` must be created with
       :meth:`qarnot.connection.Connection.create_pool`
       or retrieved with :meth:`qarnot.connection.Connection.pools` or :meth:`qarnot.connection.Connection.retrieve_pool`.
    """
    def __init__(self, connection, name, profile, instancecount):
        self._name = name
        self._state = 'UnSubmitted'  # RO property same for below
        self._profile = profile
        self._connection = connection
        self.constants = {}
        """
         :type: dict(str, str)

         Constants of the task.
         Can be set until :meth:`submit` is called

        .. note:: See available constants for a specific profile
              with :meth:`qarnot.connection.Connection.retrieve_profile`.
        """
        self.constraints = {}
        self._auto_update = True
        self._last_auto_update_state = self._auto_update
        self._update_cache_time = 5

        self._last_cache = time.time()
        self._instancecount = instancecount
        self._resource_objects_ids = []
        self._resource_type = None
        self._resource_objects = []
        self._tags = []
        self._creation_date = None
        self._uuid = None
        self._max_objects_exceptions_class = MaxPoolException

    @classmethod
    def _retrieve(cls, connection, uuid):
        """Retrieve a submitted pool given its uuid.

        :param qarnot.connection.Connection connection:
          the cluster to retrieve the pool from
        :param str uuid: the uuid of the pool to retrieve

        :rtype: Pool
        :returns: The retrieved pool.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingPoolException: no such pool
        """
        resp = connection._get(get_url('pool update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingPoolException(resp.json()['message'])
        raise_on_error(resp)
        return Pool.from_json(connection, resp.json())

    @classmethod
    def from_json(cls, connection, json_pool):
        """Create a Pool object from a json pool.

        :param qarnot.connection.Connection connection: the cluster connection
        :param dict json_pool: Dictionary representing the pool
        :returns: The created :class:`~qarnot.pool.Pool`.
        """
        new_pool = cls(connection,
                       json_pool['name'],
                       json_pool['profile'],
                       json_pool['instanceCount'])
        new_pool._update(json_pool)
        return new_pool

    def _update(self, json_pool):
        """Update this pool from retrieved info."""
        self._name = json_pool['name']
        self._profile = json_pool['profile']
        self._instancecount = json_pool['instanceCount']

        if 'resourceDisks' in json_pool and json_pool['resourceDisks'] is not None:
            self._resource_objects_ids = json_pool['resourceDisks']
            self._resource_type = Disk
        if 'resourceBuckets' in json_pool and json_pool['resourceBuckets'] is not None:
            self._resource_objects_ids = json_pool['resourceBuckets']
            self._resource_type = Bucket

        if len(self._resource_objects_ids) != \
                len(self._resource_objects):
            del self._resource_objects[:]

        if 'status' in json_pool:
            self._status = json_pool['status']
        self._creation_date = datetime.datetime.strptime(json_pool['creationDate'], "%Y-%m-%dT%H:%M:%SZ")

        for constant in json_pool['constants']:
            self.constants[constant.get('key')] = constant.get('value')
        self._uuid = json_pool['uuid']
        self._state = json_pool['state']
        self._tags = json_pool.get('tags', None)

    def _to_json(self):
        """Get a dict ready to be json packed from this pool."""
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]
        constr_list = [
            {'key': key, 'value': value}
            for key, value in self.constraints.items()
        ]

        json_pool = {
            'name': self._name,
            'profile': self._profile,
            'constants': const_list,
            'constraints': constr_list,
            'instanceCount': self._instancecount,
            'tags': self._tags
        }
        alldisk = all(isinstance(x, Disk) for x in self._resource_objects)
        allbucket = all(isinstance(x, Bucket) for x in self._resource_objects)

        if alldisk or allbucket:
            self._resource_objects_ids = [x.uuid for x in self._resource_objects]
        else:
            raise ValueError("Can't mix Buckets and Disks as resources")
        if allbucket:
            self._resource_type = Bucket
            json_pool['resourceBuckets'] = self._resource_objects_ids
        if alldisk:
            self._resource_type = Disk
            json_pool['resourceDisks'] = self._resource_objects_ids
        return json_pool

    def submit(self):
        """Submit pool to the cluster if it is not already submitted.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.MaxPoolException: Pool quota reached
        :raises qarnot.exceptions.NotEnoughCreditsException: Not enough credits
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingDiskException:
          resource disk is not a valid disk

        .. note:: Will ensure all added files are on the resource disk
           regardless of their uploading mode.
        """
        if self._uuid is not None:
            return self._state
        for rdisk in self.resources:
            rdisk.flush()
        payload = self._to_json()
        resp = self._connection._post(get_url('pools'), json=payload)

        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'])
        elif resp.status_code == 403:
            if resp.json()['message'].startswith('Maximum number of disks reached'):
                raise MaxDiskException(resp.json()['message'])
            else:
                raise MaxPoolException(resp.json()['message'])
        elif resp.status_code == 402:
            raise NotEnoughCreditsException(resp.json()['message'])
        raise_on_error(resp)
        self._uuid = resp.json()['uuid']
        self.update(True)

    def update(self, flushcache=False):
        """
        Update the pool object from the REST Api.
        The flushcache parameter can be used to force the update, otherwise a cached version of the object
        will be served when accessing properties of the object.
        Cache behavior is configurable with :attr:`auto_update` and :attr:`update_cache_time`.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: pool does not represent a
          valid one
        """
        if self._uuid is None:
            return

        now = time.time()
        if (now - self._last_cache) < self._update_cache_time and not flushcache:
            return

        resp = self._connection._get(
            get_url('pool update', uuid=self._uuid))
        if resp.status_code == 404:
            raise MissingPoolException(resp.json()['message'])

        raise_on_error(resp)
        self._update(resp.json())
        self._last_cache = time.time()

    def delete(self, purge_resources=False):
        """Delete this pool on the server.

        :param bool purge_resources: parameter value is used to determine if the disk is also deleted.
                Defaults to False.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: pool does not exist
        """
        if self._uuid is None:
            return

        if purge_resources and self.resources is not None:
            rdisks = []
            for duuid in self._resource_objects_ids:
                try:
                    d = Disk._retrieve(self._connection, duuid)
                    rdisks.append(d)
                except MissingDiskException as exception:
                    pass

        resp = self._connection._delete(get_url('pool update', uuid=self._uuid))
        if resp.status_code == 404:
            raise self._max_objects_exceptions_class(resp.json()['message'])
        raise_on_error(resp)

        if purge_resources and self.resources is not None:
            toremove = []
            for rdisk in rdisks:
                try:
                    rdisk.update()
                    rdisk.delete()
                    toremove.append(rdisk)
                except (MissingDiskException, LockedDiskException) as exception:
                    warnings.warn(str(exception))
            for tr in toremove:
                rdisks.remove(tr)
            self.resources = rdisks

        self._state = "Deleted"
        self._uuid = None

    def close(self):
        """Close this pool if running.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingPoolException: pool does not exist
        """
        self.update(True)

        resp = self._connection._post(
            get_url('pool close', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingPoolException(resp.json()['message'])
        raise_on_error(resp)

        self.update(True)

    @property
    def uuid(self):
        return self._uuid

    @property
    def state(self):
        """:type: :class:`str`
        :getter: return this pool's state

        """
        if self._auto_update:
            self.update()
        return self._state

    @property
    def resources(self):
        """:type: list(:class:`~qarnot.disk.Disk`)
        :getter: Returns this pool's resources disks
        :setter: Sets this pool's resources disks

        Represents resource files.
        """
        if self._auto_update:
            self.update()

        if not self._resource_objects:
            if self._resource_type == Disk:
                for duuid in self._resource_objects_ids:
                    d = Disk._retrieve(self._connection, duuid)
                    self._resource_objects.append(d)
            elif self._resource_type == Bucket:
                for bid in self._resource_objects_ids:
                    d = Bucket(self._connection, bid)
                    self._resource_objects.append(d)

        return self._resource_objects

    @resources.setter
    def resources(self, value):
        """This is a setter."""
        self._resource_objects = value

    @property
    def name(self):
        """:type: :class:`str`
        :getter: Returns this pool's name
        :setter: Sets this pool's name

        The pool's name.

        Can be set until pool is submitted.
        """
        return self._name

    @name.setter
    def name(self, value):
        """Setter for name."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")
        else:
            self._name = value

    @property
    def tags(self):
        """:type: :class:list(`str`)
        :getter: Returns this pool's tags
        :setter: Sets this pool's tags

        Custom tags.
        """
        if self._auto_update:
            self.update()

        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value
        self._auto_update = False

    @property
    def profile(self):
        """:type: :class:`str`
        :getter: Returns this pool's profile
        :setter: Sets this pool's profile

        The profile to run the pool with.

        Can be set until :meth:`submit` is called.
        """
        return self._profile

    @profile.setter
    def profile(self, value):
        """setter for profile"""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")
        else:
            self._profile = value

    @property
    def instancecount(self):
        """:type: :class:`int`
        :getter: Returns this pool's instance count
        :setter: Sets this pool's instance count

        Number of instances needed for the pool.

        Can be set until :meth:`submit` is called.
        """
        return self._instancecount

    @instancecount.setter
    def instancecount(self, value):
        """Setter for instancecount."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")
        self._instancecount = value

    @property
    def creation_date(self):
        """:type: :class:`str`

        :getter: Returns this pool's creation date

        Creation date of the pool (UTC Time)
        """
        return self._creation_date

    @property
    def status(self):
        """:type: :class:`qarnot.status.Status`
        :getter: Returns this pool's status

        Status of the task
        """
        if self._auto_update:
            self.update()

        if self._status:
            return Status(self._status)
        return self._status

    @property
    def auto_update(self):
        """:type: :class:`bool`

        :getter: Returns this pool's auto update state
        :setter: Sets this pool's auto update state

        Auto update state, default to True
        When auto update is disabled properties will always return cached value
        for the object and a call to :meth:`update` will be required to get latest values from the REST Api.
        """
        return self._auto_update

    @auto_update.setter
    def auto_update(self, value):
        """Setter for auto_update feature
        """
        self._auto_update = value
        self._last_auto_update_state = self._auto_update

    @property
    def update_cache_time(self):
        """:type: :class:`int`

        :getter: Returns this pool's auto update state
        :setter: Sets this pool's auto update state

        Cache expiration time, default to 5s
        """
        return self._update_cache_time

    @update_cache_time.setter
    def update_cache_time(self, value):
        """Setter for update_cache_time
        """
        self._update_cache_time = value
