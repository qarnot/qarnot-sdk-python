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

from . import raise_on_error, get_url, _util
from .bucket import Bucket
from .status import Status
from .exceptions import MissingPoolException, MaxPoolException, NotEnoughCreditsException, \
    BucketStorageUnavailableException, MissingBucketException


class Pool(object):
    """Represents a Qarnot pool.

    .. note::
       A :class:`Pool` must be created with
       :meth:`qarnot.connection.Connection.create_pool`
       or retrieved with :meth:`qarnot.connection.Connection.pools` or :meth:`qarnot.connection.Connection.retrieve_pool`.
    """

    def __init__(self, connection, name, profile, instancecount=1, shortname=None):
        """Create a new :class:`Pool`.

        :param connection: the cluster on which to send the pool
        :type connection: :class:`qarnot.connection.Connection`
        :param name: given name of the pool
        :type name: :class:`str`
        :param profile: which profile to use with this task
        :type profile: :class:`str`

        :param instancecount: number of instances or ranges on which to run pool
        :type instancecount: int or str
        :param shortname: userfriendly pool name
        :type shortname: :class:`str`
        """

        self._name = name
        self._shortname = shortname
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
        self._resource_object_ids = []
        self._resource_objects = []
        self._tags = []
        self._creation_date = None
        self._uuid = None
        self._max_objects_exceptions_class = MaxPoolException
        self._is_summary = False

        self._is_elastic = False
        self._elastic_minimum_slots = 0
        self._elastic_maximum_slots = 1
        self._elastic_minimum_idle_slots = 0
        self._elastic_resize_period = 90
        self._elastic_resize_factor = 1
        self._elastic_minimum_idle_time = 0

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
    def from_json(cls, connection, json_pool, is_summary=False):
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
        new_pool._is_summary = is_summary
        return new_pool

    def _update(self, json_pool):
        """Update this pool from retrieved info."""
        self._name = json_pool['name']
        self._shortname = json_pool.get('shortname')
        self._profile = json_pool['profile']
        self._instancecount = json_pool['instanceCount']

        if 'resourceBuckets' in json_pool and json_pool['resourceBuckets'] is not None:
            self._resource_object_ids = json_pool['resourceBuckets']

        if 'status' in json_pool:
            self._status = json_pool['status']
        self._creation_date = _util.parse_datetime(json_pool['creationDate'])

        if 'constants' in json_pool:
            for constant in json_pool['constants']:
                self.constants[constant.get('key')] = constant.get('value')
        self._uuid = json_pool['uuid']
        self._state = json_pool['state']
        self._tags = json_pool.get('tags', None)

        if 'elasticProperty' in json_pool:
            elasticProperty = json_pool["elasticProperty"]
            self._is_elastic = elasticProperty["isElastic"]
            self._elastic_maximum_slots = elasticProperty["maxTotalSlots"]
            self._elastic_minimum_slots = elasticProperty["minTotalSlots"]
            self._elastic_minimum_idle_slots = elasticProperty["minIdleSlots"]
            self._elastic_minimum_idle_time = elasticProperty["minIdleTimeSeconds"]
            self._elastic_resize_factor = elasticProperty["rampResizeFactor"]
            self._elastic_resize_period = elasticProperty["resizePeriod"]

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

        elastic_dict = {
            "isElastic": self._is_elastic,
            "minTotalSlots": self._elastic_minimum_slots,
            "maxTotalSlots": self._elastic_maximum_slots,
            "minIdleSlots": self._elastic_minimum_idle_slots,
            "resizePeriod": self._elastic_resize_period,
            "rampResizeFactor": self._elastic_resize_factor,
            "minIdleTimeSeconds": self._elastic_minimum_idle_time
        }

        json_pool = {
            'name': self._name,
            'profile': self._profile,
            'constants': const_list,
            'constraints': constr_list,
            'instanceCount': self._instancecount,
            'tags': self._tags,
            'elasticProperty': elastic_dict
        }

        if self._shortname is not None:
            json_pool['shortname'] = self._shortname

        json_pool['resourceBuckets'] = self._resource_object_ids

        return json_pool

    def submit(self):
        """Submit pool to the cluster if it is not already submitted.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.MaxPoolException: Pool quota reached
        :raises qarnot.exceptions.NotEnoughCreditsException: Not enough credits
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: Will ensure all added files are on the resource bucket
           regardless of their uploading mode.
        """
        if self._uuid is not None:
            return self._state
        for bucket in self.resources:
            bucket.flush()
        payload = self._to_json()
        resp = self._connection._post(get_url('pools'), json=payload)

        if resp.status_code == 404:
            raise MissingBucketException(resp.json()['message'])
        elif resp.status_code == 403:
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
        self._is_summary = False
        self._last_cache = time.time()

    def apply_elastic_settings(self):
        response = self._connection._put('pool update', json=self._to_json())
        if response.status_code == 404:
            raise MissingPoolException(response.json()['message'])

        raise_on_error(response)
        self.update()

    def setup_elastic(self, minimum_total_slots=0, maximum_total_slots=1, minimum_idle_slots=0, minimum_idle_time_seconds=0, resize_factor=1, resize_period=90):
        self._is_elastic = True
        self._elastic_maximum_slots = maximum_total_slots
        self._elastic_minimum_slots = minimum_total_slots
        self._elastic_minimum_idle_slots = minimum_idle_slots
        self._elastic_minimum_idle_time = minimum_idle_time_seconds
        self._elastic_resize_factor = resize_factor
        self._elastic_resize_period = resize_period

    def delete(self, purge_resources=False):
        """Delete this pool on the server.

        :param bool purge_resources: parameter value is used to determine if the bucket is also deleted.
                Defaults to False.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: pool does not exist
        """
        if purge_resources:
            self._update_if_summary()
        if self._uuid is None:
            return

        resp = self._connection._delete(get_url('pool update', uuid=self._uuid))
        if resp.status_code == 404:
            raise self._max_objects_exceptions_class(resp.json()['message'])
        raise_on_error(resp)

        if purge_resources and len(self.resources) != 0:
            toremove = []
            for r in self.resources:
                try:
                    r.update()
                    r.delete()
                    toremove.append(r)
                except (MissingBucketException, BucketStorageUnavailableException) as exception:
                    warnings.warn(str(exception))
            for tr in toremove:
                self.resources.remove(tr)

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
        """:type: :class:`str`
        :getter: Returns this pool's uuid

        The pool's uuid.

        Automatically set when a pool is submitted.
        """
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
        """:type: list(:class:`~qarnot.bucket.Bucket`)
        :getter: Returns this pool's resources bucket
        :setter: Sets this pool's resources bucket

        Represents resource files.
        """
        if self._auto_update:
            self.update()
        if not self._resource_objects:
            for bid in self._resource_object_ids:
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
    def shortname(self):
        """:type: :class:`str`
        :getter: Returns this pool's shortname
        :setter: Sets this pool's shortname

        The pool's shortname, must be DNS compliant and unique, if not provided, will default to :attr:`uuid`.

        Can be set until pool is submitted.
        """
        return self._shortname

    @shortname.setter
    def shortname(self, value):
        """Setter for shortname."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")
        else:
            self._shortname = value

    @property
    def tags(self):
        """:type: :class:list(`str`)
        :getter: Returns this pool's tags
        :setter: Sets this pool's tags

        Custom tags.
        """
        self._update_if_summary()
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
        self._update_if_summary()
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

    def _update_if_summary(self):
        """Trigger flush update if the task is made from a summary.

        This should be called before accessing any fields not contained in a summary task
        """
        if self._is_summary:
            self.update(True)

    @property
    def is_elastic(self):
        return self._is_elastic

    @is_elastic.setter
    def is_elastic(self, value):
        self._is_elastic = value

    @property
    def elastic_minimum_slots(self):
        return self._elastic_minimum_slots

    @elastic_minimum_slots.setter
    def elastic_minimum_slots(self, value):
        self._elastic_minimum_slots = value

    @property
    def elastic_maximum_slots(self):
        return self._elastic_maximum_slots

    @elastic_maximum_slots.setter
    def elastic_maximum_slots(self, value):
        self._elastic_maximum_slots = value

    @property
    def elastic_minimum_idle_slots(self):
        return self._elastic_minimum_idle_slots

    @elastic_minimum_idle_slots.setter
    def elastic_minimum_idle_slots(self, value):
        self._elastic_minimum_idle_slots = value

    @property
    def elastic_minimum_idle_time(self):
        return self._elastic_minimum_idle_time

    @elastic_minimum_idle_time.setter
    def elastic_minimum_idle_time(self, value):
        self._elastic_minimum_idle_time = value

    @property
    def elastic_resize_factor(self):
        return self._elastic_resize_factor

    @elastic_resize_factor.setter
    def elastic_resize_factor(self, value):
        if value <= 0:
            raise Exception("resize factor must be > 0")
        elif value > 1:
            raise Exception("resize factor must be <= 1")
        self._elastic_resize_factor = value

    @property
    def elastic_resize_period(self):
        return self._elastic_resize_period

    @elastic_resize_period.setter
    def elastic_resize_period(self, value):
        self._elastic_resize_period = value

    def __repr__(self):
        return '{0} - {1} - {2} - {3} - {5} - InstanceCount : {4} - Resources : {6} '\
            'Tag {7} - IsElastic {8} - ElasticMin {9} - ElasticMax {10} - ElasticMinIdle {11} -'\
            ' ElasticResizePeriod {12} - ElasticResizeFactor {13} - ElasticMinIdleTimeSeconds {14}'\
            .format(self.name,
                    self.shortname,
                    self._uuid,
                    self._profile,
                    self._instancecount,
                    self.state,
                    (self._resource_object_ids if self._resource_objects is not None else ""),
                    self._tags,
                    self._is_elastic,
                    self._elastic_minimum_slots,
                    self._elastic_maximum_slots,
                    self._elastic_minimum_idle_slots,
                    self._elastic_resize_period,
                    self._elastic_resize_factor,
                    self._elastic_minimum_idle_time)
