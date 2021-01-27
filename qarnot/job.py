"""Module to handle a job."""

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
import datetime


from .task import Task
from . import get_url, raise_on_error, _util
from .exceptions import MaxJobException, NotEnoughCreditsException, MissingJobException, UnauthorizedException


class JobState:
    Active = "Active"
    Terminating = "Terminating"
    Completed = "Completed"
    Deleting = "Deleting"


class Job(object):
    """Represents a Qarnot job.

    .. note::
       A :class:`Job` must be created with
       :meth:`qarnot.connection.Connection.create_job`
       or retrieved with :meth:`qarnot.connection.Connection.jobs` or :meth:`qarnot.connection.Connection.retrieve_job`.
    """
    def __init__(self, connection, name, pool=None, shortname=None, use_dependencies=False):
        """Create a new :class:`Job`.

        :param connection: the cluster on which to send the job
        :type connection: :class:`qarnot.connection.Connection`
        :param name: given name of the job
        :type name: :class:`str`
        :param pool: which Pool to submit the job in,
        :type pool: :class:`~qarnot.pool.Pool` or None
        :param shortname: userfriendly job name
        :type shortname: :class:`str`
        :param use_dependencies: allow dependencies between tasks in this job
        :type job: :class:`bool`
        """
        self._connection = connection
        self._name = name
        self._shortname = shortname
        self._pool_uuid = None
        if pool is not None:
            if _util.is_string(pool):
                self._pool_uuid = pool
            else:
                self._pool_uuid = pool.uuid
        self._state = ""
        self._uuid = None
        self._creation_date = datetime.datetime.now()
        self._use_dependencies = use_dependencies
        self._max_wall_time = None
        self._update_cache_time = 5
        self._auto_update = True
        self._last_auto_update_state = self._auto_update

        self._last_cache = time.time()
        self._completion_time_to_live = "00:00:00"
        self._auto_delete = False

    @property
    def auto_update(self):
        """:type: :class:`bool`

        :getter: Returns this job's auto update state
        :setter: Sets this job's auto update state

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

        :getter: Returns this job's auto update state
        :setter: Sets this job's auto update state

        Cache expiration time, default to 5s
        """
        return self._update_cache_time

    @property
    def state(self):
        """:type: :class:`str`
        :getter: return this job's state

        State of the job.

        Value is in
           * UnSubmitted
           * Active,
           * Terminating,
           * Completed,
           * Deleting

        .. warning::
           this is the state of the job when the object was retrieved,
           call :meth:`update` for up to date value.
        """
        if self._auto_update:
            self.update()
        return self._state

    @property
    def tasks(self):
        """:type: List of :class:`~qarnot.task.Task`
        :getter: Returns this job tasks

        The tasks submitted in this job.
        """
        if self._uuid is None:
            return
        response = self._connection._get(get_url('job tasks', uuid=self._uuid))
        if response.status_code == 404:
            raise MissingJobException(response.json()['message'])
        raise_on_error(response)
        return [Task.from_json(self, task, True) for task in response.json()]

    @property
    def use_dependencies(self):
        """:type: :class:`bool`
        :getter: task's job can have dependencies
        :setter: Set if there is task's job dependencies

        Can be set until :meth:`submit` is called.
        """
        return self._use_dependencies

    @use_dependencies.setter
    def use_dependencies(self, value):
        """setter for job"""
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        else:
            self._use_dependencies = value

    @property
    def uuid(self):
        """:type: :class:`str`
        :getter: Returns this job's uuid

        The job's uuid.

        Automatically set when a job is submitted.
        """
        return self._uuid

    @property
    def name(self):
        """:type: :class:`str`
        :getter: Returns this job's name
        :setter: Sets this job's name

        The job's name.

        Can be set until job is submitted.
        """
        return self._name

    @name.setter
    def name(self, value):
        """Setter for name."""
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        else:
            self._name = value

    @property
    def shortname(self):
        """:type: :class:`str`
        :getter: Returns this job's shortname
        :setter: Sets this job's shortname

        The job's shortname, must be DNS compliant and unique, if not provided, will default to :attr:`uuid`.

        Can be set until job is submitted.
        """
        return self._shortname

    @shortname.setter
    def shortname(self, value):
        """Setter for shortname."""
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        else:
            self._shortname = value

    @property
    def creation_date(self):
        """:type: :class:`str`

        :getter: Returns this job's creation date

        Creation date of the job (UTC Time)
        """
        return self._creation_date

    @property
    def max_wall_time(self):
        """:type: :class:`str`
        :getter: Returns this job's maximum wall time
        :setter: Sets this job's maximum wall time

        The job's maximum wall time.
        It is a time span string.
        Format example: 'd.hh:mm:ss' or 'hh:mm:ss'

        Can be set until job is submitted.
        """
        return self._max_wall_time

    @max_wall_time.setter
    def max_wall_time(self, value):
        """Setter for maximum wall time. In time span format example : 'd.hh:mm:ss' or 'hh:mm:ss' """
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        elif _util.is_string(value):
            self._max_wall_time = value
        elif isinstance(value, datetime.timedelta):
            self._max_wall_time = _util.convert_timedelta_to_timespan_string(value)
        else:
            raise TypeError("Maximum wall time must be a time span format string (example: 'd.hh:mm:ss' or 'hh:mm:ss')")

    @property
    def pool(self):
        """:type: :class:`~qarnot.pool.Pool`
        :getter: Returns this job's pool
        :setter: Sets this job's pool

        The pool to run the job in.

        Can be set until :meth:`submit` is called.
        """
        return self._connection.retrieve_pool(self._pool_uuid)

    @pool.setter
    def pool(self, value):
        """setter for pool"""
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        else:
            self._pool_uuid = value.uuid

    @staticmethod
    def _retrieve(connection, uuid):
        resp = connection._get(get_url('job update', uuid=uuid))
        """Retrieve a submitted job given its uuid.

        :param qarnot.connection.Connection connection:
          the cluster to retrieve the job from
        :param str uuid: the uuid of the job to retrieve

        :rtype: Job
        :returns: The retrieved job.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingJobException: no such job
        """
        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])
        raise_on_error(resp)
        return Job.from_json(connection, resp.json())

    @classmethod
    def from_json(cls, connection, payload):
        """Create a Job object from a json job.

        :param qarnot.connection.Connection connection: the cluster connection
        :param dict json_job: Dictionary representing the job
        :returns: The created :class:`~qarnot.job.Job`.
        """
        job = cls(connection,
                  payload["name"],
                  payload["poolUuid"],
                  payload["shortname"],
                  payload["useDependencies"])

        job._uuid = payload["uuid"]
        job._state = payload["state"]
        job._creation_date = payload["creationDate"]
        job._last_modified = payload["lastModified"]
        job._max_wall_time = _util.parse_timedelta(payload["maxWallTime"])

        job._auto_delete = payload["autoDeleteOnCompletion"]
        job._completion_time_to_live = payload["completionTimeToLive"]
        return job

    def _to_json(self):
        """Get a dict ready to be json packed from this task."""
        json_job = {
            'name': self._name,
            'poolUuid': self._pool_uuid,
            'shortname': self._shortname,
            'state': self._state,
            'useDependencies': self._use_dependencies,
            'maxWallTime': self._max_wall_time,
            'autoDeleteOnCompletion': self._auto_delete,
            'completionTimeToLive': self._completion_time_to_live
        }

        return json_job

    def _update(self, json_job):
        """Update this job from retrieved info."""
        self._uuid = json_job['uuid']
        self._name = json_job['name']
        self._shortname = json_job.get('shortname')
        self._pool_uuid = json_job.get('poolUuid')
        self._use_dependencies = json_job.get('useDependencies')
        self._state = json_job['state']
        self._creation_date = _util.parse_datetime(json_job['creationDate'])
        self._last_modified = json_job.get('lastModified')
        self._max_wall_time = json_job.get('maxWallTime')
        self._creation_date = _util.parse_datetime(json_job['creationDate'])

    def submit(self):
        """Submit job to the cluster if it is not already submitted.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.MaxJobException: Job quota reached
        :raises qarnot.exceptions.NotEnoughCreditsException: Not enough credits
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        """
        if self._uuid is not None and self._uuid != "":
            return self._state
        payload = self._to_json()
        resp = self._connection._post(get_url('jobs'), json=payload)

        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])
        elif resp.status_code == 403:
            raise MaxJobException(resp.json()['message'])
        elif resp.status_code == 402:
            raise NotEnoughCreditsException(resp.json()['message'])
        raise_on_error(resp)
        self._uuid = resp.json()['uuid']
        self.update()

    def update(self, flushcache=False):
        """
        Update the job object from the REST Api.
        The flushcache parameter can be used to force the update, otherwise a cached version of the object
        will be served when accessing properties of the object.
        Cache behavior is configurable with :attr:`auto_update` and :attr:`update_cache_time`.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingJobException: job does not exist
        """
        if self._uuid is None:
            return

        now = time.time()
        if (now - self._last_cache) < self._update_cache_time and not flushcache:
            return

        resp = self._connection._get(
            get_url('job update', uuid=self._uuid))
        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])

        raise_on_error(resp)
        self._update(resp.json())
        self._last_cache = time.time()

    def terminate(self):
        """Terminate this job on the server and abort all remaining tasks in the job.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingJobException: job does not exist
        """

        if self._uuid is None:
            return
        resp = self._connection._post(get_url('job terminate', uuid=self._uuid))
        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])
        raise_on_error(resp)
        self._state = JobState.Terminating

    def delete(self, forceAbort=False):
        """Delete this job on the server.

        The forceAbort parameter can be used to force running task in the job to be aborted,

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.UnauthorizedException: job still contains running tasks
        :raises qarnot.exceptions.MissingJobException: job does not exist
        """

        if self._uuid is None:
            return
        resp = self._connection._delete(get_url('job delete', uuid=self._uuid, force=forceAbort))
        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])
        elif resp.status_code == 403:
            raise UnauthorizedException(resp.json()['message'])
        raise_on_error(resp)
        self._state = JobState.Deleting
        self._uuid = None

    @property
    def auto_delete(self):
        """Autodelete this job if it is finished and your max number of job is reach

        Can be set until :meth:`submit` is called.

        :type: :class:`bool`
        :getter: Returns is this job must autodelete
        :setter: Sets this job's autodelete
        :default_value: "False"

        :raises AttributeError: if you try to reset the auto_delete after the job is submit
        """
        return self._auto_delete

    @auto_delete.setter
    def auto_delete(self, value):
        """Setter for auto_delete, this can only be set before job's submission
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched job")
        self._auto_delete = value

    @property
    def completion_ttl(self):
        """The job will be auto delete `completion_ttl` after it is finished

        Can be set until :meth:`submit` is called.

        :getter:  Returns this job's completed time to live.
        :type: :class:`str`
        :setter: Sets this job's this job's completed time to live.
        :type: :class:`str` or :class:`datetime.timedelta`
        :default_value: ""

        :raises AttributeError: if you try to set it after the job is submitted

        The `completion_ttl` must be a timedelta or a time span format string (example: 'd.hh:mm:ss' or 'hh:mm:ss')
        """
        return self._completion_time_to_live

    @completion_ttl.setter
    def completion_ttl(self, value):
        """Setter for completion_ttl, this can only be set before job's submission"""
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        self._completion_time_to_live = _util.parse_to_timespan_string(value)

    def __repr__(self):
        return '{0} - {1} - {2} - Pool : {3} - {4} - UseDependencies : {5} '\
            .format(self.name,
                    self.shortname,
                    self._uuid,
                    self._pool_uuid,
                    self.state,
                    self._use_dependencies)
