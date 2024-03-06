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
from typing import Dict, List, Optional

from qarnot.retry_settings import RetrySettings
from qarnot.forced_network_rule import ForcedNetworkRule
from qarnot.secrets import SecretsAccessRights

from . import raise_on_error, get_url, _util
from .bucket import Bucket
from .status import Status
from .hardware_constraint import HardwareConstraint
from .scheduling_type import SchedulingType
from .privileges import Privileges
from .error import Error
from .exceptions import MissingPoolException, MaxPoolException, NotEnoughCreditsException, \
    BucketStorageUnavailableException, MissingBucketException, MissingPoolInstanceException, UnauthorizedException


class Pool(object):
    """Represents a Qarnot pool.

    .. note::
       A :class:`Pool` must be created with
       :meth:`qarnot.connection.Connection.create_pool`
       or retrieved with :meth:`qarnot.connection.Connection.pools` or :meth:`qarnot.connection.Connection.retrieve_pool`.
    """

    def __init__(self, connection, name, profile, instancecount=1, shortname=None, scheduling_type: SchedulingType = None):
        """Create a new :class:`Pool`.

        :param connection: the cluster on which to send the pool
        :type connection: :class:`~qarnot.connection.Connection`
        :param name: given name of the pool
        :type name: :class:`str`
        :param profile: which profile to use with this task
        :type profile: :class:`str`

        :param instancecount: number of instances or ranges on which to run pool
        :type instancecount: int or str
        :param shortname: userfriendly pool name
        :type shortname: :class:`str`

        :param logger: which job to attach the task to
        :type logger: :class:`logging.Logger`
        """

        self._name = name
        self._shortname = shortname
        self._state = 'UnSubmitted'  # RO property same for below
        self._profile = profile
        self._connection = connection
        self._constants: Dict[str, str] = {}
        self._status = None
        """
         :type: dict(str, str)

         Constants of the pool.
         Can be set until :meth:`submit` is called

        .. note:: See available constants for a specific profile
              with :meth:`qarnot.connection.Connection.retrieve_profile`.
        """
        self._constraints: Dict[str, str] = {}
        self._labels: Dict[str, str] = {}
        self._auto_update = True
        self._last_auto_update_state = self._auto_update
        self._update_cache_time = 5
        self._scheduling_type = scheduling_type
        self._targeted_reserved_machine_key: str = None

        self._last_cache = time.time()
        self._instancecount = instancecount
        self._resource_object_advanced: List[Bucket] = []
        self._resource_object_ids: List[str] = []
        self._resource_objects: List[Bucket] = []
        self._tags: List[str] = []
        self._errors: Optional[List[Error]] = None
        self._creation_date = None
        self._uuid = None
        self._is_summary = False
        self._preparation_task: Dict[str, str] = None
        self._status = None

        self._is_elastic = False
        self._elastic_minimum_slots = 0
        self._elastic_maximum_slots = 1
        self._elastic_minimum_idle_slots = 0
        self._elastic_resize_period = 90
        self._elastic_resize_factor = 1
        self._elastic_minimum_idle_time = 0
        self._running_core_count = 0
        self._running_instance_count = 0
        self._pool_usage = 0.0
        self._total_slot_capacity = 0
        self._queued_or_running_task_instances_count = 0.0

        self._completion_time_to_live = "00:00:00"
        self._auto_delete = False
        self._tasks_wait_for_synchronization = False

        self._previous_state = None
        self._state_transition_time = None
        self._previous_state_transition_time = None
        self._last_modified = None
        self._execution_time = None
        self._end_date = None
        self._hardware_constraints: List[HardwareConstraint] = []
        self._default_resources_cache_ttl_sec: Optional[int] = None
        self._privileges: Privileges = Privileges()
        self._default_retry_settings: RetrySettings = RetrySettings()
        self._forced_network_rules: List[ForcedNetworkRule] = []
        self._secrets_access_rights: SecretsAccessRights = SecretsAccessRights()

    @classmethod
    def _retrieve(cls, connection, uuid):
        """Retrieve a submitted pool given its uuid.

        :param qarnot.connection.Connection connection:
          the cluster to retrieve the pool from
        :param str uuid: the uuid of the pool to retrieve

        :rtype: Pool
        :returns: The retrieved pool.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.UnauthorizedException: invalid operation on non running pool
        :raises ~qarnot.exceptions.MissingPoolException: no such pool
        """
        resp = connection._get(get_url('pool update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingPoolException(_util.get_error_message_from_http_response(resp))
        elif resp.status_code == 403:
            raise UnauthorizedException(_util.get_error_message_from_http_response(resp))
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

        if json_pool.get('runningCoreCount') is not None:
            self._running_core_count = json_pool['runningCoreCount']
        if json_pool.get('runningInstanceCount') is not None:
            self._running_instance_count = json_pool['runningInstanceCount']

        if 'errors' in json_pool:
            self._errors = [Error(d) for d in json_pool['errors']]
        else:
            self._errors = []

        if 'resourceBuckets' in json_pool and json_pool['resourceBuckets'] is not None:
            self._resource_object_ids = json_pool['resourceBuckets']

        if 'advancedResourceBuckets' in json_pool and json_pool['advancedResourceBuckets']:
            self._resource_object_advanced = json_pool['advancedResourceBuckets']

        if 'status' in json_pool:
            self._status = json_pool['status']
        self._creation_date = _util.parse_datetime(json_pool['creationDate'])

        if 'constants' in json_pool:
            for constant in json_pool['constants']:
                self._constants[constant.get('key')] = constant.get('value')

        self._uuid = json_pool['uuid']
        self._state = json_pool['state']
        self._preparation_task = json_pool.get('preparationTask')
        self._tags = json_pool.get('tags', None)
        self._tasks_wait_for_synchronization = json_pool.get('taskDefaultWaitForPoolResourcesSynchronization', False)
        self._pool_usage = json_pool.get("poolUsage", 0.0)
        self._total_slot_capacity = json_pool.get("totalSlotCapacity", 0)
        self._queued_or_running_task_instances_count = json_pool.get("queuedOrRunningTaskInstancesCount", 0.0)

        if 'autoDeleteOnCompletion' in json_pool:
            self._auto_delete = json_pool["autoDeleteOnCompletion"]
        if 'completionTimeToLive' in json_pool:
            self._completion_time_to_live = json_pool["completionTimeToLive"]

        if 'elasticProperty' in json_pool:
            elasticProperty = json_pool["elasticProperty"]
            self._is_elastic = elasticProperty["isElastic"]
            self._elastic_maximum_slots = elasticProperty["maxTotalSlots"]
            self._elastic_minimum_slots = elasticProperty["minTotalSlots"]
            self._elastic_minimum_idle_slots = elasticProperty["minIdleSlots"]
            self._elastic_minimum_idle_time = elasticProperty["minIdleTimeSeconds"]
            self._elastic_resize_factor = elasticProperty["rampResizeFactor"]
            self._elastic_resize_period = elasticProperty["resizePeriod"]

        self._previous_state = json_pool.get('previousState', None)
        self._state_transition_time = json_pool.get('stateTransitionTime', None)
        self._previous_state_transition_time = json_pool.get('previousStateTransitionTime', None)
        self._last_modified = json_pool.get('lastModified', None)
        self._execution_time = json_pool.get('executionTime', None)
        self._end_date = json_pool.get('endDate', None)
        self._labels = json_pool.get('labels', {})
        self._hardware_constraints = [HardwareConstraint.from_json(hw_constraint_dict) for hw_constraint_dict in json_pool.get("hardwareConstraints", [])]
        self._default_resources_cache_ttl_sec = json_pool.get("defaultResourcesCacheTTLSec", None)
        self._targeted_reserved_machine_key = json_pool.get("targetedReservedMachineKey", None)
        if 'privileges' in json_pool:
            self._privileges = Privileges.from_json(json_pool["privileges"])
        if 'defaultRetrySettings' in json_pool:
            self._default_retry_settings = RetrySettings.from_json(json_pool["defaultRetrySettings"])
        if 'schedulingType' in json_pool:
            self._scheduling_type = SchedulingType.from_string(json_pool["schedulingType"])
        self._forced_network_rules = [ForcedNetworkRule.from_json(forced_network_dict) for forced_network_dict in json_pool.get("forcedNetworkRules", [])]
        if 'secretsAccessRights' in json_pool:
            self._secrets_access_rights = SecretsAccessRights.from_json(json_pool["secretsAccessRights"])

    def _to_json(self):
        """Get a dict ready to be json packed from this pool."""
        const_list = [
            {'key': key, 'value': value}
            for key, value in self._constants.items()
        ]
        constr_list = [
            {'key': key, 'value': value}
            for key, value in self._constraints.items()
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
            'preparationTask': self._preparation_task,
            'elasticProperty': elastic_dict,
            'taskDefaultWaitForPoolResourcesSynchronization': self._tasks_wait_for_synchronization,
            'labels': self._labels,
        }

        if self._shortname is not None:
            json_pool['shortname'] = self._shortname

        self._resource_object_advanced = [x.to_json() for x in self._resource_objects]
        json_pool['advancedResourceBuckets'] = self._resource_object_advanced

        json_pool['autoDeleteOnCompletion'] = self._auto_delete
        json_pool['completionTimeToLive'] = self._completion_time_to_live
        json_pool['hardwareConstraints'] = [x.to_json() for x in self._hardware_constraints]
        json_pool['defaultResourcesCacheTTLSec'] = self._default_resources_cache_ttl_sec
        json_pool['privileges'] = self._privileges.to_json()
        json_pool['defaultRetrySettings'] = self._default_retry_settings.to_json()

        if self._scheduling_type is not None:
            json_pool['schedulingType'] = self._scheduling_type.schedulingType

        if self._targeted_reserved_machine_key is not None:
            json_pool['targetedReservedMachineKey'] = self._targeted_reserved_machine_key

        if self._forced_network_rules is not None:
            json_pool['forcedNetworkRules'] = [x.to_json() for x in self._forced_network_rules]

        if self._secrets_access_rights:
            json_pool['secretsAccessRights'] = self._secrets_access_rights.to_json()

        return json_pool

    def submit(self):
        """Submit pool to the cluster if it is not already submitted.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.MaxPoolException: Pool quota reached
        :raises ~qarnot.exceptions.NotEnoughCreditsException: Not enough credits
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingBucketException: resource bucket not found

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
            raise MissingBucketException(_util.get_error_message_from_http_response(resp))
        elif resp.status_code == 403:
            error_message = _util.get_error_message_from_http_response(resp)
            if "maximum number of pools reached" in error_message.lower():
                raise MaxPoolException(error_message)
            raise UnauthorizedException(error_message)
        elif resp.status_code == 402:
            raise NotEnoughCreditsException(_util.get_error_message_from_http_response(resp))
        raise_on_error(resp)
        self._uuid = resp.json()['uuid']
        self.update(True)

    def update(self, flushcache=False):
        """
        Update the pool object from the REST Api.
        The flushcache parameter can be used to force the update, otherwise a cached version of the object
        will be served when accessing properties of the object.
        Cache behavior is configurable with :attr:`auto_update` and :attr:`update_cache_time`.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not represent a
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
            raise MissingPoolException(_util.get_error_message_from_http_response(resp))

        raise_on_error(resp)
        self._update(resp.json())
        self._is_summary = False
        self._last_cache = time.time()

    def commit(self):
        """Replicate local changes on the current object instance to the REST API

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist

        This function need to be call to apply the local elastic pool setting modifications.
        .. note:: When updating buckets' properties, auto update will be disabled until commit is called.
        """
        response = self._connection._put(get_url('pool update', uuid=self._uuid), json=self._to_json())
        self._auto_update = self._last_auto_update_state

        if response.status_code == 404:
            raise MissingPoolException(_util.get_error_message_from_http_response(response))
        raise_on_error(response)

    def update_resources(self):
        """ Update resources for a running pool.

        The typical workflow is as follows:
           1. Upload new files on your resource bucket,
           2. Call this method,
           3. The new files will appear on all the compute nodes in the same resources folder as original resources

        Note: There is no way to know when the files are effectively transfered. This information is available on the compute node only.
        Note: The update is additive only: files deleted from the bucket will NOT be deleted from the pool's resources directory.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist
        """

        self.update(True)
        resp = self._connection._patch(get_url('pool update', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingPoolException(_util.get_error_message_from_http_response(resp))
        raise_on_error(resp)

        self.update(True)

    def setup_elastic(self, minimum_total_slots=0, maximum_total_slots=1, minimum_idle_slots=0, minimum_idle_time_seconds=0, resize_factor=1, resize_period=90):
        """Setup the pool elastic properties

        :param int minimum_total_slots: Minimum slot number for the pool in elastic mode.
                Defaults to 0.
        :param int maximum_total_slots: Maximum slot number for the pool in elastic mode.
                Defaults to 1.
        :param int minimum_idle_slots: Minimum idling slot number.
                Defaults to 0.
        :param int minimum_idle_time_seconds: Wait time in seconds before closing an unused slot if the number of unused slots are upper than the minimum_idle_slots.
                Defaults to 0.
        :param float resize_factor: Growing factor of the pool. It must be a number between 0 and 1.
                Defaults to 1.
        :param int resize_period: Refresh rate of resizing the pool in elastic mode.
                Defaults to 90.
        """
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

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist
        """
        if purge_resources:
            self._update_if_summary()

        if self._auto_update:
            self._auto_update = False

        if self._uuid is None:
            return

        resp = self._connection._delete(get_url('pool update', uuid=self._uuid))
        if resp.status_code == 404:
            raise MissingPoolException(_util.get_error_message_from_http_response(resp))
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

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.UnauthorizedException: invalid operation on non running pool
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist
        """
        self.update(True)

        resp = self._connection._post(
            get_url('pool close', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingPoolException(_util.get_error_message_from_http_response(resp))
        elif resp.status_code == 403:
            raise UnauthorizedException(_util.get_error_message_from_http_response(resp))
        raise_on_error(resp)

        self.update(True)

    def stdout(self, instanceId: Optional[int] = None):
        """Get the standard output of the pool, or of a specific instance
        of the pool, since the submission of the pool.

        :rtype: :class:`str`
        :returns: The standard output.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist
        :raises ~qarnot.exceptions.MissingPoolInstanceException: pool instance does not exist

        .. note:: The buffer is circular, if stdout is too big, prefer calling
          :meth:`fresh_stdout` regularly.
        """
        if self._uuid is None:
            return ""
        if instanceId is not None:
            resp = self._connection._get(
                get_url('pool instance stdout', uuid=self._uuid, instanceId=instanceId))
            if resp.status_code == 404:
                raise MissingPoolInstanceException(_util.get_error_message_from_http_response(resp))
        else:
            resp = self._connection._get(
                get_url('pool stdout', uuid=self._uuid))
            if resp.status_code == 404:
                raise MissingPoolException(_util.get_error_message_from_http_response(resp))

        raise_on_error(resp)

        return resp.text

    def fresh_stdout(self, instanceId: Optional[int] = None):
        """Get what has been written on the standard output since last time
        the output of the pool or of the instance was retrieved.

        :rtype: :class:`str`
        :returns: The new output since last call.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist
        :raises ~qarnot.exceptions.MissingPoolInstanceException: pool instance does not exist
        """
        if self._uuid is None:
            return ""
        if instanceId is not None:
            resp = self._connection._post(
                get_url('pool instance stdout', uuid=self._uuid, instanceId=instanceId))
            if resp.status_code == 404:
                raise MissingPoolInstanceException(_util.get_error_message_from_http_response(resp))
        else:
            resp = self._connection._post(
                get_url('pool stdout', uuid=self._uuid))
            if resp.status_code == 404:
                raise MissingPoolException(_util.get_error_message_from_http_response(resp))

        raise_on_error(resp)
        return resp.text

    def stderr(self, instanceId: Optional[int] = None):
        """Get the standard error of the pool, or of a specific instance
        of the pool, since the submission of the pool.

        :rtype: :class:`str`
        :returns: The standard error.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist
        :raises ~qarnot.exceptions.MissingPoolInstanceException: pool instance does not exist

        .. note:: The buffer is circular, if stderr is too big, prefer calling
          :meth:`fresh_stderr` regularly.
        """
        if self._uuid is None:
            return ""
        if instanceId is not None:
            resp = self._connection._get(
                get_url('pool instance stderr', uuid=self._uuid, instanceId=instanceId))
            if resp.status_code == 404:
                raise MissingPoolInstanceException(_util.get_error_message_from_http_response(resp))
        else:
            resp = self._connection._get(
                get_url('pool stderr', uuid=self._uuid))
            if resp.status_code == 404:
                raise MissingPoolException(_util.get_error_message_from_http_response(resp))

        raise_on_error(resp)
        return resp.text

    def fresh_stderr(self, instanceId: Optional[int] = None):
        """Get what has been written on the standard error since last time
        the standard error of the pool or of its instance was retrieved.

        :rtype: :class:`str`
        :returns: The new error messages since last call.

        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises ~qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises ~qarnot.exceptions.MissingPoolException: pool does not exist
        :raises ~qarnot.exceptions.MissingPoolInstanceException: pool instance does not exist
        """
        if self._uuid is None:
            return ""
        if instanceId is not None:
            resp = self._connection._post(
                get_url('pool instance stderr', uuid=self._uuid, instanceId=instanceId))
            if resp.status_code == 404:
                raise MissingPoolInstanceException(_util.get_error_message_from_http_response(resp))
        else:
            resp = self._connection._post(
                get_url('pool stderr', uuid=self._uuid))
            if resp.status_code == 404:
                raise MissingPoolException(_util.get_error_message_from_http_response(resp))

        raise_on_error(resp)
        return resp.text

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

        State of the pool.

        Value is in
           * UnSubmitted
           * Submitted
           * PartiallyDispatched
           * FullyDispatched
           * PartiallyExecuting
           * FullyExecuting
           * Closing
           * Closed
           * Failure
           * PendingDelete

        .. warning::
           this is the state of the pool when the object was retrieved,
           call :meth:`update` for up to date value.
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
            for adv in self._resource_object_advanced:
                d = Bucket.from_json(self._connection, adv)
                self._resource_objects.append(d)

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
        """Setter for tags"""
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
    def running_core_count(self):
        """:type: :class:`int`
        :getter: Returns this pool's running core count

        Number of core running inside the pool.
        """
        return self._running_core_count

    @property
    def running_instance_count(self):
        """:type: :class:`int`
        :getter: Returns this pool's running instance count

        Number of instances running inside the pool.
        """
        return self._running_instance_count

    @property
    def errors(self):
        """:type: list(:class:`str`)
        :getter: Returns this pool's error list

        Error reason if any, empty string if none
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._errors

    @property
    def creation_date(self):
        """:type: :class:`str`

        :getter: Returns this pool's creation date

        Creation date of the pool (UTC Time)
        """
        return self._creation_date

    @property
    def status(self):
        """:type: :class:`~qarnot.status.Status`
        :getter: Returns this pool's status

        Status of the pool
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
        """:type: :class:`bool`
        :getter: Returns this pool's is_elastic
        :setter: Sets this pool's is_elastic

        Define if you use a static or an elastic pool.
        """
        return self._is_elastic

    @is_elastic.setter
    def is_elastic(self, value):
        self._is_elastic = value

    @property
    def elastic_minimum_slots(self):
        """:type: :class:`int`
        :getter: Returns this pool's elastic_minimum_slots
        :setter: Sets this pool's elastic_minimum_slots

        The minimum slot number of the elastic pool.
        Define the minimum number of pool instances stay open during the pool execution.
        """
        return self._elastic_minimum_slots

    @elastic_minimum_slots.setter
    def elastic_minimum_slots(self, value):
        """Setter for elastic_minimum_slots"""
        self._elastic_minimum_slots = value

    @property
    def elastic_maximum_slots(self):
        """:type: :class:`int`
        :getter: Returns this pool's elastic_maximum_slots
        :setter: Sets this pool's elastic_maximum_slots

        The maximum slot number of the elastic pool.
        Define the maximum number of pool instances opened during the pool execution.
        """
        return self._elastic_maximum_slots

    @elastic_maximum_slots.setter
    def elastic_maximum_slots(self, value):
        """Setter for elastic_maximum_slots"""
        self._elastic_maximum_slots = value

    @property
    def elastic_minimum_idle_slots(self):
        """:type: :class:`int`
        :getter: Returns this pool's elastic_minimum_idle_slots
        :setter: Sets this pool's elastic_minimum_idle_slots

        The minimum idle number of the elastic pool.
        Define the minimum number of the idle pool instances stay opened during the pool execution.
        It should be lower to elastic_minimum_slots to be usefull
        """
        return self._elastic_minimum_idle_slots

    @elastic_minimum_idle_slots.setter
    def elastic_minimum_idle_slots(self, value):
        """Setter for elastic_minimum_idle_slots"""
        self._elastic_minimum_idle_slots = value

    @property
    def elastic_minimum_idle_time(self):
        """:type: :class:`int`
        :getter: Returns this pool's elastic_minimum_idle_time
        :setter: Sets this pool's elastic_minimum_idle_time

        Wait time in seconds before closing an unused slot if the number of unused slots are upper than the minimum_idle_slots.
        """
        return self._elastic_minimum_idle_time

    @elastic_minimum_idle_time.setter
    def elastic_minimum_idle_time(self, value):
        """Setter for elastic_minimum_idle_time"""
        self._elastic_minimum_idle_time = value

    @property
    def elastic_resize_factor(self):
        """:type: :class:`float`
        :getter: Returns this pool's elastic_resize_factor
        :setter: Sets this pool's elastic_resize_factor

        The resize factor of the pool.
        It represent the resize factor of the slots.
        It's a decimal number upper than 0 and and equal or lower the 1
        """
        return self._elastic_resize_factor

    @elastic_resize_factor.setter
    def elastic_resize_factor(self, value):
        """Setter for elastic_resize_factor

        :raises Exception: resize factor must be > 0
        :raises Exception: resize factor must be <= 1
        """
        if value <= 0:
            raise ValueError("resize factor must be > 0")
        elif value > 1:
            raise ValueError("resize factor must be <= 1")
        self._elastic_resize_factor = value

    @property
    def elastic_resize_period(self):
        """:type: :class:`int`
        :getter: Returns this pool's elastic_resize_period
        :setter: Sets this pool's elastic_resize_period

        The resize period of the elastic pool in second.
        This is the refresh rate of resizing the elastic pool.
        """
        return self._elastic_resize_period

    @elastic_resize_period.setter
    def elastic_resize_period(self, value):
        """Setter for elastic_resize_period"""
        self._elastic_resize_period = value

    @property
    def preparation_command_line(self):
        """:type: :class:`str`:
        :getter: Returns this pool's command line.
        :setter: set the pool's command line.

        Update the pool command line if needed
        The command line is a command executed on the node before any task is executed.
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        if self._preparation_task:
            return self._preparation_task["commandLine"]
        return None

    @preparation_command_line.setter
    def preparation_command_line(self, value):
        """Setter for command line
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")
        self._update_if_summary()
        if self._auto_update:
            self.update()
        if self._preparation_task:
            self._preparation_task["commandLine"] = value
        else:
            self._preparation_task = {"commandLine": value}

    @property
    def constants(self):
        """:type: dictionary{:class:`str` : :class:`str`}
        :getter: Returns this pool's constants dictionary.
        :setter: set the pool's constants dictionary.

        Update the constants if needed.
        Constants are used to configure the profiles,
        set them to change your profile's parameters.
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._constants

    @constants.setter
    def constants(self, value):
        """Setter for constants
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        self._constants = value

    @property
    def constraints(self):
        """:type: dictionary{:class:`str` : :class:`str`}
        :getter: Returns this pool's constraints dictionary.
        :setter: set the pool's constraints dictionary.

        Update the constraints if needed
        advance usage
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._constraints

    @constraints.setter
    def constraints(self, value):
        """Setter for constraints
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        self._constraints = value

    @property
    def secrets_access_rights(self):
        """:type: :class:`~qarnot.secrets.SecretsAccessRights`
        :getter: Returns the description of the secrets the tasks in this pool will have access to when running.
        :setter: set the secrets this pool will have access to when running.

        Secrets can be accessible either by exact match on the key or by using a prefix
        in order to match all the secrets starting with said prefix.
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._secrets_access_rights

    @secrets_access_rights.setter
    def secrets_access_rights(self, value: SecretsAccessRights):
        """Setter for secrets access rights
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        self._secrets_access_rights = value

    @property
    def forced_network_rules(self):
        """:type: list{:class:`~qarnot.forced_network_rule.ForcedNetworkRule`}
        :getter: Returns this pool's forced network rules list.
        :setter: set the pool's forced network rules list.

        Update the forced network rules if needed.
        Forced network rules are reserved for internal use.
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._forced_network_rules

    @forced_network_rules.setter
    def forced_network_rules(self, value: List["ForcedNetworkRule"]):
        """Setter for forced_constants
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")
        self._forced_network_rules = value

    @property
    def labels(self):
        """:type: dictionary{:class:`str` : :class:`str`}
        :getter: Return this pool's labels dictionary.
        :setter: set the pool's labels constraints dictionary.

        Labels are used to attach arbitrary key / value pairs
        to a pool in order to find them later with greater ease.
        They do not affect the execution of a pool.
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._labels

    @labels.setter
    def labels(self, value):
        """Setter for labels
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")

        self._labels = value

    @property
    def tasks_default_wait_for_pool_resources_synchronization(self):
        """:type: :class:`bool`
        :getter: Returns this task's tasks_default_wait_for_pool_resources_synchronization.
        :setter: set the task's tasks_default_wait_for_pool_resources_synchronization.

        :raises AttributeError: can't set this attribute on a launched task
        """
        return self._tasks_wait_for_synchronization

    @tasks_default_wait_for_pool_resources_synchronization.setter
    def tasks_default_wait_for_pool_resources_synchronization(self, value):
        """Setter for tasks_default_wait_for_pool_resources_synchronization
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        self._tasks_wait_for_synchronization = value

    @property
    def auto_delete(self):
        """Autodelete this pool if it is finished and your max number of pool is reach

        Can be set until :meth:`submit` is called.

        :type: :class:`bool`
        :getter: Returns is this pool must autodelete
        :setter: Sets this pool's autodelete
        :default_value: "False"

        :raises AttributeError: if you try to reset the auto_delete after the pool is submit
        """
        self._update_if_summary()
        return self._auto_delete

    @auto_delete.setter
    def auto_delete(self, value):
        """Setter for auto_delete, this can only be set before pool's submission
        """
        self._update_if_summary()
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")
        self._auto_delete = value

    @property
    def completion_ttl(self):
        """The pool will be auto delete `completion_ttl` after it is finished

        Can be set until :meth:`submit` is called.

        :getter:  Returns this pool's completed time to live.
        :type: :class:`str`
        :setter: Sets this pool's this pool's completed time to live.
        :type: :class:`str` or :class:`datetime.timedelta`
        :default_value: ""

        :raises AttributeError: if you try to set it after the pool is submitted

        The `completion_ttl` must be a timedelta or a time span format string (example: ``d.hh:mm:ss`` or ``hh:mm:ss`` )
        """
        self._update_if_summary()
        return self._completion_time_to_live

    @completion_ttl.setter
    def completion_ttl(self, value):
        """Setter for completion_ttl, this can only be set before pool's submission"""
        self._update_if_summary()
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        self._completion_time_to_live = _util.parse_to_timespan_string(value)

    @property
    def previous_state(self):
        """
        :type: :class:`str`
        :getter: Returns the running pool's previous state
        """
        self._update_if_summary()
        return self._previous_state

    @property
    def state_transition_time(self):
        """
        :type: :class:`str`
        :getter: Returns the running pool's transition state time

        pool state transition time (UTC Time)
        """
        self._update_if_summary()
        return self._state_transition_time

    @property
    def previous_state_transition_time(self):
        """
        :type: :class:`str`
        :getter: Returns the running pool's previous transition state time

        pool previous state transition time (UTC Time)
        """
        self._update_if_summary()
        return self._previous_state_transition_time

    @property
    def last_modified(self):
        """
        :type: :class:`str`
        :getter: Returns the running pool's last modification time

        pool's last modified time (UTC Time)
        """
        self._update_if_summary()
        return self._last_modified

    @property
    def execution_time(self):
        """
        :type: :class:`str`
        :getter: Returns the running pool's total CPU execution time.

        pool's execution time of all it's instances.
        """
        self._update_if_summary()
        return self._execution_time

    @property
    def end_date(self):
        """
        :type: :class:`str`
        :getter: Returns the finished pool's end date.

        pool's end date (UTC Time)
        """
        self._update_if_summary()
        return self._end_date

    @property
    def pool_usage(self):
        """
        :type: :class:`float`
        :getter: Returns the pool usage
        """
        self._update_if_summary()
        return self._pool_usage

    @property
    def total_slot_capacity(self):
        """
        :type: :class:`int`
        :getter: Returns the pool slot capacity
        """
        self._update_if_summary()
        return self._total_slot_capacity

    @property
    def queued_or_running_task_instances_count(self):
        """
        :type: :class:`int`
        :getter: Returns count of task instances dispatched in the pool
        """
        return self._queued_or_running_task_instances_count

    @property
    def hardware_constraints(self):
        """:type: :class:`list`, optional

        :getter: setup the hardware constraints
        :setter: Set up specific hardware constraints.

        :raises AttributeError: trying to set this after the task is submitted
        """
        return self._hardware_constraints

    @hardware_constraints.setter
    def hardware_constraints(self, value):
        """Setter for hardware_constraints
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")

        self._hardware_constraints = value

    @property
    def default_resources_cache_ttl_sec(self) -> Optional[int]:
        """:type: :class:`int`, optional

        :getter: The default time to live used for all the pool resources cache

        :raises AttributeError: trying to set this after the task is submitted
        """
        return self._default_resources_cache_ttl_sec

    @default_resources_cache_ttl_sec.setter
    def default_resources_cache_ttl_sec(self, value: Optional[int]):
        """Setter for default_resources_cache_ttl_sec
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")

        self._default_resources_cache_ttl_sec = value

    @property
    def privileges(self) -> Privileges:
        """:type: :class:`~qarnot.privileges.Privileges`

        :getter: The privileges granted to the pool

        :raises AttributeError: trying to set this after the pool is submitted
        """
        return self._privileges

    @privileges.setter
    def privileges(self, value: Privileges):
        """Setter for privileges
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")

        self._privileges = value

    def allow_credentials_to_be_exported_to_pool_environment(self):
        """Grant privilege to export api and storage credentials to the pool environment"""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")

        if self._privileges is None:
            self._privileges = Privileges()

        self._privileges._exportApiAndStorageCredentialsInEnvironment = True

    @property
    def default_retry_settings(self) -> RetrySettings:
        """:type: :class:`~qarnot.retry_settings.RetrySettings`

        :getter: The default retry settings applied to the pool's tasks

        :raises AttributeError: trying to set this after the task is submitted
        """
        return self._default_retry_settings

    @default_retry_settings.setter
    def default_retry_settings(self, value: RetrySettings):
        """Setter for default_retry_settings
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")

        self._default_retry_settings = value

    @property
    def scheduling_type(self) -> SchedulingType:
        """:type: :class:`~qarnot.scheduling_type.SchedulingType`

        :getter: The scheduling type for the pool

        :raises AttributeError: trying to set this after the pool is submitted
        """
        return self._scheduling_type

    @scheduling_type.setter
    def scheduling_type(self, value: SchedulingType):
        """Setter for scheduling_type
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")

        self._scheduling_type = value

    @property
    def targeted_reserved_machine_key(self) -> str:
        """:type: :class:`str`

        :getter: The reserved machine key when using the "reserved" scheduling type

        :raises AttributeError: trying to set this after the pool is submitted
        """
        return self._targeted_reserved_machine_key

    @targeted_reserved_machine_key.setter
    def targeted_reserved_machine_key(self, value: str):
        """Setted for targeted_reserved_machine_key
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched pool")

        self._targeted_reserved_machine_key = value

    def __repr__(self):
        return '{0} - {1} - {2} - {3} - {5} - InstanceCount : {4} - Resources : {6} '\
            'Tag {7} - IsElastic {8} - ElasticMin {9} - ElasticMax {10} - ElasticMinIdle {11} -'\
            ' ElasticResizePeriod {12} - ElasticResizeFactor {13} - ElasticMinIdleTimeSeconds {14} - '\
            'Errors {15}'\
            .format(self.name,
                    self.shortname,
                    self._uuid,
                    self._profile,
                    self._instancecount,
                    self.state,
                    ([bucket._uuid for bucket in self._resource_objects] if self._resource_objects is not None else ""),
                    self._tags,
                    self._is_elastic,
                    self._elastic_minimum_slots,
                    self._elastic_maximum_slots,
                    self._elastic_minimum_idle_slots,
                    self._elastic_resize_period,
                    self._elastic_resize_factor,
                    self._elastic_minimum_idle_time,
                    self._errors)
