"""Module to handle a task."""

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


from os import makedirs, path
import time
import warnings
import sys

from . import get_url, raise_on_error, _util
from .status import Status
from .bucket import Bucket
from .pool import Pool
from .error import Error
from .exceptions import MissingTaskException, MaxTaskException, NotEnoughCreditsException, \
    MissingBucketException, BucketStorageUnavailableException

try:
    from progressbar import AnimatedMarker, Bar, Percentage, AdaptiveETA, ProgressBar
except ImportError:
    pass

RUNNING_DOWNLOADING_STATES = ['Submitted', 'PartiallyDispatched',
                              'FullyDispatched', 'PartiallyExecuting',
                              'FullyExecuting', 'DownloadingResults', 'UploadingResults']


class Task(object):
    """Represents a Qarnot task.

    .. note::
       A :class:`Task` must be created with
       :meth:`qarnot.connection.Connection.create_task`
       or retrieved with :meth:`qarnot.connection.Connection.tasks` or :meth:`qarnot.connection.Connection.retrieve_task`.
    """
    def __init__(self, connection, name, profile_or_pool=None, instancecount_or_range=1, shortname=None, job=None):
        """Create a new :class:`Task`.

        :param connection: the cluster on which to send the task
        :type connection: :class:`qarnot.connection.Connection`
        :param name: given name of the task
        :type name: :class:`str`
        :param profile_or_pool: which profile to use with this task, or which Pool to run task,
        :type profile_or_pool: str or :class:`~qarnot.pool.Pool` or None

        :param instancecount_or_range: number of instances or ranges on which to run task
        :type instancecount_or_range: int or str
        :param shortname: userfriendly task name
        :type shortname: :class:`str`
        :param job: which job to attach the task to
        :type job: :class:`~qarnot.job.Job`
        """
        self._name = name
        self._shortname = shortname
        self._profile = None
        self._pool_uuid = None
        self._job_uuid = None
        if profile_or_pool is not None:
            if isinstance(profile_or_pool, Pool):
                self._pool_uuid = profile_or_pool.uuid
            else:
                self._profile = profile_or_pool

        if job is not None:
            if isinstance(profile_or_pool, Pool):
                raise Exception("Cannot attach a same task to pool and a job simultaneously")
            self._job_uuid = job.uuid

        if isinstance(instancecount_or_range, int):
            self._instancecount = instancecount_or_range
            self._advanced_range = None
        else:
            self._advanced_range = instancecount_or_range
            self._instancecount = 0

        self._running_core_count = 0
        self._running_instance_count = 0

        self._resource_objects = []

        self._result_object = None
        self._connection = connection
        self._constants = {}
        """
         :type: dict(str,str)

         Constants of the task.
         Can be set until :meth:`run` or :meth:`submit` is called

        .. note:: See available constants for a specific profile
              with :meth:`qarnot.connection.Connection.retrieve_profile`.
        """

        self._dependentOn = []

        self._auto_update = True
        self._last_auto_update_state = self._auto_update
        self._update_cache_time = 5

        self._last_cache = time.time()
        self._constraints = {}
        self._state = 'UnSubmitted'  # RO property same for below
        self._uuid = None
        self._snapshots = False
        self._dirty = False
        self._rescount = -1
        self._snapshot_whitelist = None
        self._snapshot_blacklist = None
        self._results_whitelist = None
        self._results_blacklist = None
        self._status = None
        self._completed_instances = []
        self._tags = []
        self._creation_date = None
        self._errors = None
        self._resource_object_ids = []
        self._result_object_id = None
        self._is_summary = False
        self._completion_time_to_live = "00:00:00"
        self._auto_delete = False
        self._wait_for_pool_resources_synchronization = None

    @classmethod
    def _retrieve(cls, connection, uuid):
        """Retrieve a submitted task given its uuid.

        :param qarnot.connection.Connection connection:
          the cluster to retrieve the task from
        :param str uuid: the uuid of the task to retrieve

        :rtype: Task
        :returns: The retrieved task.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: no such task
        """
        resp = connection._get(get_url('task update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])
        raise_on_error(resp)
        return Task.from_json(connection, resp.json())

    def run(self, output_dir=None, job_timeout=None, live_progress=False, results_progress=None):
        """Submit a task, wait for the results and download them if required.

        :param str output_dir: (optional) path to a directory that will contain the results
        :param float job_timeout: (optional) Number of seconds before the task :meth:`abort` if it is not
          already finished
        :param bool live_progress: (optional) display a live progress
        :param results_progress: (optional) can be a callback (read,total,filename) or True to display a progress bar
        :type results_progress: bool or function(float, float, str)
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.MaxTaskException: Task quota reached
        :raises qarnot.exceptions.NotEnoughCreditsException: Not enough credits
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: Will ensure all added file are on the resource bucket
           regardless of their uploading mode.
        .. note:: If this function is interrupted (script killed for example),
           but the task is submitted, the task will still be executed remotely
           (results will not be downloaded)
        .. warning:: Will override *output_dir* content.
        """
        self.submit()
        self.wait(timeout=job_timeout, live_progress=live_progress)
        if job_timeout is not None:
            self.abort()
        if output_dir is not None:
            self.download_results(output_dir, progress=results_progress)

    def resume(self, output_dir, job_timeout=None, live_progress=False, results_progress=None):
        """Resume waiting for this task if it is still in submitted mode.
        Equivalent to :meth:`wait` + :meth:`download_results`.

        :param str output_dir: path to a directory that will contain the results
        :param float job_timeout: Number of seconds before the task :meth:`abort` if it is not
          already finished
        :param bool live_progress: display a live progress
        :param results_progress: can be a callback (read,total,filename) or True to display a progress bar
        :type results_progress: bool or function(float, float, str)
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist

        .. note:: Do nothing if the task has not been submitted.
        .. warning:: Will override *output_dir* content.
        """
        if self._uuid is None:
            return output_dir
        self.wait(timeout=job_timeout, live_progress=live_progress)
        self.download_results(output_dir, progress=results_progress)

    def submit(self):
        """Submit task to the cluster if it is not already submitted.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.MaxTaskException: Task quota reached
        :raises qarnot.exceptions.NotEnoughCreditsException: Not enough credits
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: Will ensure all added files are on the resource bucket
           regardless of their uploading mode.

        .. note:: To get the results, call :meth:`download_results` once the job is done.
        """
        self._pre_submit()

        payload = self._to_json()
        resp = self._connection._post(get_url('tasks'), json=payload)

        if resp.status_code == 404:
            raise MissingBucketException(resp.json()['message'])
        elif resp.status_code == 403:
            raise MaxTaskException(resp.json()['message'])
        elif resp.status_code == 402:
            raise NotEnoughCreditsException(resp.json()['message'])
        raise_on_error(resp)
        self._uuid = resp.json()['uuid']

        self._post_submit()

    def _pre_submit(self):
        """Pre submit action on the task & its resources"""
        if self._uuid is not None:
            return self._state
        for resource_buckets in self.resources:
            resource_buckets.flush()

    def _post_submit(self):
        """Post submit action on the task after submission"""
        if not isinstance(self._snapshots, bool):
            self.snapshot(self._snapshots)

        self.update(True)

    def abort(self):
        """Abort this task if running.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist
        """
        self.update(True)

        resp = self._connection._post(
            get_url('task abort', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])
        raise_on_error(resp)

        self.update(True)

    def update_resources(self):
        """ Update resources for a running task.

        The typical workflow is as follows:
           1. Upload new files on your resource bucket,
           2. Call this method,
           3. The new files will appear on all the compute nodes in the $DOCKER_WORKDIR folder
        Note: There is no way to know when the files are effectively transfered. This information is available on the compute node only.
        Note: The update is additive only: files deleted from the bucket will NOT be deleted from the task's resources directory.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist
        """

        self.update(True)
        resp = self._connection._patch(
            get_url('task update', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])
        raise_on_error(resp)

        self.update(True)

    def delete(self, purge_resources=False, purge_results=False):
        """Delete this task on the server.

        :param bool purge_resources: parameter value is used to determine if the bucket is also deleted.
                Defaults to False.

        :param bool purge_results: parameter value is used to determine if the bucket is also deleted.
                Defaults to False.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist
        """
        if purge_resources or purge_results:
            self._update_if_summary()

        if self._auto_update:
            self._auto_update = False

        if self._uuid is None:
            return

        if purge_results and self.results is not None:
            try:
                self.results.update()
            except MissingBucketException:
                purge_results = False

        resp = self._connection._delete(
            get_url('task update', uuid=self._uuid))
        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])
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

        if purge_results and self._result_object is not None:
            try:
                self._result_object.delete()
                self._result_object = None
            except MissingBucketException as exception:
                warnings.warn(str(exception))

        self._state = "Deleted"
        self._uuid = None

    def update(self, flushcache=False):
        """
        Update the task object from the REST Api.
        The flushcache parameter can be used to force the update, otherwise a cached version of the object
        will be served when accessing properties of the object.
        Some methods will flush the cache, like :meth:`submit`, :meth:`abort`, :meth:`wait` and :meth:`instant`.
        Cache behavior is configurable with :attr:`auto_update` and :attr:`update_cache_time`.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not represent a
          valid one
        """
        if self._uuid is None:
            return

        now = time.time()
        if (now - self._last_cache) < self._update_cache_time and not flushcache:
            return

        resp = self._connection._get(
            get_url('task update', uuid=self._uuid))
        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])

        raise_on_error(resp)
        self._update(resp.json())
        self._last_cache = time.time()
        self._is_summary = False

    def _update(self, json_task):
        """Update this task from retrieved info."""
        self._name = json_task['name']
        self._shortname = json_task.get('shortname')
        self._profile = json_task['profile']
        self._pool_uuid = json_task.get('poolUuid')
        self._job_uuid = json_task.get('jobUuid')
        self._instancecount = json_task.get('instanceCount')
        self._advanced_range = json_task.get('advancedRanges')
        self._wait_for_pool_resources_synchronization = json_task.get('waitForPoolResourcesSynchronization', None)

        if json_task['runningCoreCount'] is not None:
            self._running_core_count = json_task['runningCoreCount']
        if json_task['runningInstanceCount'] is not None:
            self._running_instance_count = json_task['runningInstanceCount']

        if 'resourceBuckets' in json_task and json_task['resourceBuckets']:
            self._resource_object_ids = json_task['resourceBuckets']

        if 'resultBucket' in json_task and json_task['resultBucket']:
            self._result_object_id = json_task['resultBucket']

        if 'status' in json_task:
            self._status = json_task['status']
        self._creation_date = _util.parse_datetime(json_task['creationDate'])
        if 'errors' in json_task:
            self._errors = [Error(d) for d in json_task['errors']]
        else:
            self._errors = []

        if 'constants' in json_task:
            for constant in json_task['constants']:
                self._constants[constant.get('key')] = constant.get('value')

        self._uuid = json_task['uuid']
        self._state = json_task['state']
        self._tags = json_task.get('tags', None)
        if 'resultsCount' in json_task:
            if self._rescount < json_task['resultsCount']:
                self._dirty = True
            self._rescount = json_task['resultsCount']

        if 'resultsBlacklist' in json_task:
            self._results_blacklist = json_task['resultsBlacklist']
        if 'resultsWhitelist' in json_task:
            self._results_whitelist = json_task['resultsWhitelist']
        if 'snapshotWhitelist' in json_task:
            self._snapshot_whitelist = json_task['snapshotWhitelist']
        if 'snapshotBlacklist' in json_task:
            self._snapshot_blacklist = json_task['snapshotBlacklist']

        if 'completedInstances' in json_task:
            self._completed_instances = [CompletedInstance(x) for x in json_task['completedInstances']]
        else:
            self._completed_instances = []

        if 'autoDeleteOnCompletion' in json_task:
            self._auto_delete = json_task["autoDeleteOnCompletion"]
        if 'completionTimeToLive' in json_task:
            self._completion_time_to_live = json_task["completionTimeToLive"]

    @classmethod
    def from_json(cls, connection, json_task, is_summary=False):
        """Create a Task object from a json task.

        :param qarnot.connection.Connection connection: the cluster connection
        :param dict json_task: Dictionary representing the task
        :returns: The created :class:`~qarnot.task.Task`.
        """
        if 'instanceCount' in json_task:
            instance_count_or_range = json_task['instanceCount']
        else:
            instance_count_or_range = json_task['advancedRanges']
        new_task = cls(connection,
                       json_task['name'],
                       json_task.get('profile') or json_task.get('poolUuid'),
                       instance_count_or_range)
        new_task._update(json_task)
        new_task._is_summary = is_summary
        return new_task

    def commit(self):
        """Replicate local changes on the current object instance to the REST API

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: When updating buckets' properties, auto update will be disabled until commit is called.
        """
        data = self._to_json()
        resp = self._connection._put(get_url('task update', uuid=self._uuid), json=data)
        self._auto_update = self._last_auto_update_state
        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])

        raise_on_error(resp)

    def wait(self, timeout=None, live_progress=False):
        """Wait for this task until it is completed.

        :param float timeout: maximum time (in seconds) to wait before returning
           (None => no timeout)
        :param bool live_progress: display a live progress

        :rtype: :class:`bool`
        :returns: Is the task finished

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not represent a valid
          one
        """

        live_progress = live_progress and sys.stdout.isatty()

        if live_progress:
            try:
                widgets = [
                    Percentage(),
                    ' ', AnimatedMarker(),
                    ' ', Bar(),
                    ' ', AdaptiveETA()
                ]
                progressbar = ProgressBar(widgets=widgets, max_value=100)
            except Exception:
                live_progress = False

        start = time.time()
        if self._uuid is None:
            self.update(True)
            return False

        nap = min(10, timeout) if timeout is not None else 10

        self.update(True)
        while self._state in RUNNING_DOWNLOADING_STATES:
            if live_progress:
                n = 0
                progress = 0
                while True:
                    time.sleep(1)
                    n += 1
                    if n >= nap:
                        break
                    progress = self.status.execution_progress if self.status is not None else 0
                    progress = max(0, min(progress, 100))
                    progressbar.update(progress)
            else:
                time.sleep(nap)

            self.update(True)

            if timeout is not None:
                elapsed = time.time() - start
                if timeout <= elapsed:
                    self.update()
                    return False
                else:
                    nap = min(10, timeout - elapsed)
        self.update(True)
        if live_progress:
            progressbar.finish()
        return True

    def snapshot(self, interval):
        """Start snapshooting results.
        If called, this task's results will be periodically
        updated, instead of only being available at the end.

        Snapshots will be taken every *interval* second from the time
        the task is submitted.

        :param int interval: the interval in seconds at which to take snapshots

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not represent a
          valid one

        .. note:: To get the temporary results, call :meth:`download_results`.
        """
        if self._uuid is None:
            self._snapshots = interval
            return
        resp = self._connection._post(get_url('task snapshot', uuid=self._uuid),
                                      json={"interval": interval})

        if resp.status_code == 400:
            raise ValueError(interval)
        elif resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])

        raise_on_error(resp)

        self._snapshots = True

    def instant(self):
        """Make a snapshot of the current task.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist

        .. note:: To get the temporary results, call :meth:`download_results`.
        """
        if self._uuid is None:
            return

        resp = self._connection._post(get_url('task instant', uuid=self._uuid),
                                      json=None)

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])
        raise_on_error(resp)

        self.update(True)

    @property
    def state(self):
        """:type: :class:`str`
        :getter: return this task's state

        State of the task.

        Value is in
           * UnSubmitted
           * Submitted
           * PartiallyDispatched
           * FullyDispatched
           * PartiallyExecuting
           * FullyExecuting
           * UploadingResults
           * DownloadingResults
           * Cancelled
           * Success
           * Failure

        .. warning::
           this is the state of the task when the object was retrieved,
           call :meth:`update` for up to date value.
        """
        if self._auto_update:
            self.update()
        return self._state

    @property
    def resources(self):
        """:type: list(:class:`~qarnot.bucket.Bucket`)
        :getter: Returns this task's resources bucket
        :setter: Sets this task's resources bucket

        Represents resource files.
        """
        self._update_if_summary()
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
    def results(self):
        """:type: :class:`~qarnot.bucket.Bucket`
        :getter: Returns this task's results bucket
        :setter: Sets this task's results bucket

        Represents results files."""
        self._update_if_summary()
        if self._result_object is None and self._result_object_id is not None:
            self._result_object = Bucket(self._connection, self._result_object_id)

        if self._auto_update:
            self.update()

        return self._result_object

    @results.setter
    def results(self, value):
        """ This is a setter."""
        self._result_object = value

    def download_results(self, output_dir, progress=None):
        """Download results in given *output_dir*.

        :param str output_dir: local directory for the retrieved files.
        :param progress: can be a callback (read,total,filename)  or True to display a progress bar
        :type progress: bool or function(float, float, str)
        :raises qarnot.exceptions.MissingBucketException: the bucket is not on the server
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. warning:: Will override *output_dir* content.

        """

        if self._uuid is not None:
            self.update()

        if not path.exists(output_dir):
            makedirs(output_dir)

        if self._dirty:
            self.results.get_all_files(output_dir, progress=progress)

    def stdout(self):
        """Get the standard output of the task
        since the submission of the task.

        :rtype: :class:`str`
        :returns: The standard output.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist

        .. note:: The buffer is circular, if stdout is too big, prefer calling
          :meth:`fresh_stdout` regularly.
        """
        if self._uuid is None:
            return ""
        resp = self._connection._get(
            get_url('task stdout', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])

        raise_on_error(resp)

        return resp.text

    def fresh_stdout(self):
        """Get what has been written on the standard output since last time
        this function was called or since the task has been submitted.

        :rtype: :class:`str`
        :returns: The new output since last call.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist
        """
        if self._uuid is None:
            return ""
        resp = self._connection._post(
            get_url('task stdout', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])

        raise_on_error(resp)
        return resp.text

    def stderr(self):
        """Get the standard error of the task
        since the submission of the task.

        :rtype: :class:`str`
        :returns: The standard error.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist

        .. note:: The buffer is circular, if stderr is too big, prefer calling
          :meth:`fresh_stderr` regularly.
        """
        if self._uuid is None:
            return ""
        resp = self._connection._get(
            get_url('task stderr', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])

        raise_on_error(resp)
        return resp.text

    def fresh_stderr(self):
        """Get what has been written on the standard error since last time
        this function was called or since the task has been submitted.

        :rtype: :class:`str`
        :returns: The new error messages since last call.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: task does not exist
        """
        if self._uuid is None:
            return ""
        resp = self._connection._post(
            get_url('task stderr', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'])

        raise_on_error(resp)
        return resp.text

    @property
    def uuid(self):
        """:type: :class:`str`
        :getter: Returns this task's uuid

        The task's uuid.

        Automatically set when a task is submitted.
        """
        return self._uuid

    @property
    def name(self):
        """:type: :class:`str`
        :getter: Returns this task's name
        :setter: Sets this task's name

        The task's name.

        Can be set until task is submitted.
        """
        return self._name

    @name.setter
    def name(self, value):
        """Setter for name."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._name = value

    @property
    def shortname(self):
        """:type: :class:`str`
        :getter: Returns this task's shortname
        :setter: Sets this task's shortname

        The task's shortname, must be DNS compliant and unique, if not provided, will default to :attr:`uuid`.

        Can be set until task is submitted.
        """
        return self._shortname

    @shortname.setter
    def shortname(self, value):
        """Setter for shortname."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._shortname = value

    @property
    def tags(self):
        """:type: :class:list(`str`)
        :getter: Returns this task's tags
        :setter: Sets this task's tags

        Custom tags.
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._tags

    @tags.setter
    def tags(self, value):
        """setter for tags"""
        self._tags = value
        self._auto_update = False

    @property
    def pool(self):
        """:type: :class:`~qarnot.pool.Pool`
        :getter: Returns this task's pool
        :setter: Sets this task's pool

        The pool to run the task in.

        Can be set until :meth:`run` is called.

        .. warning:: This property is mutually exclusive with :attr:`profile`
        """
        return self._connection.retrieve_pool(self._pool_uuid)

    @pool.setter
    def pool(self, value):
        """setter for pool"""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        if self._profile is not None:
            raise AttributeError("Can't set pool if profile is not None")
        else:
            self._pool_uuid = value.uuid

    @property
    def profile(self):
        """:type: :class:`str`
        :getter: Returns this task's profile
        :setter: Sets this task's profile

        The profile to run the task with.

        Can be set until :meth:`run` or :meth:`submit` is called.

         .. warning:: This property is mutually exclusive with :attr:`pool`
        """
        return self._profile

    @profile.setter
    def profile(self, value):
        """setter for profile"""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        if self._pool_uuid is not None:
            raise AttributeError("Can't set profile if pool is not None")
        else:
            self._profile = value

    @property
    def instancecount(self):
        """:type: :class:`int`
        :getter: Returns this task's instance count
        :setter: Sets this task's instance count

        Number of instances needed for the task.

        Can be set until :meth:`run` or :meth:`submit` is called.

        :raises AttributeError: if :attr:`advanced_range` is not None when setting this property

        .. warning:: This property is mutually exclusive with :attr:`advanced_range`
        """
        return self._instancecount

    @instancecount.setter
    def instancecount(self, value):
        """Setter for instancecount."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")

        if self.advanced_range is not None:
            raise AttributeError("Can't set instancecount if advanced_range is not None")
        self._instancecount = value

    @property
    def running_core_count(self):
        """:type: :class:`int`
        :getter: Returns this task's running core count

        Number of core running inside the task.
        """
        return self._running_core_count

    @property
    def running_instance_count(self):
        """:type: :class:`int`
        :getter: Returns this task's running instance count

        Number of instances running inside the task.
        """
        return self._running_instance_count

    @property
    def advanced_range(self):
        """:type: :class:`str`
        :getter: Returns this task's advanced range
        :setter: Sets this task's advanced range

        Advanced instances range selection.

        Allows to select which instances will be computed.
        Should be None or match the following extended regular expression
        """r"""**"([0-9]+|[0-9]+-[0-9]+)(,([0-9]+|[0-9]+-[0-9]+))+"**
        eg: 1,3-8,9,12-19

        Can be set until :meth:`run` is called.

        :raises AttributeError: if :attr:`instancecount` is not 0 when setting this property

        .. warning:: This property is mutually exclusive with :attr:`instancecount`
        """
        return self._advanced_range

    @advanced_range.setter
    def advanced_range(self, value):
        """Setter for advanced_range."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        if self.instancecount != 0:
            raise AttributeError("Can't set advanced_range if instancecount is not 0")
        self._advanced_range = value

    @property
    def snapshot_whitelist(self):
        """:type: :class:`str`
        :getter: Returns this task's snapshot whitelist
        :setter: Sets this task's snapshot whitelist

        Snapshot white list (regex) for :meth:`snapshot` and :meth:`instant`

        Can be set until task is submitted.
        """
        self._update_if_summary()
        return self._snapshot_whitelist

    @snapshot_whitelist.setter
    def snapshot_whitelist(self, value):
        """Setter for snapshot whitelist, this can only be set before tasks submission
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        self._snapshot_whitelist = value

    @property
    def snapshot_blacklist(self):
        """:type: :class:`str`
        :getter: Returns this task's snapshot blacklist
        :setter: Sets this task's snapshot blacklist

        Snapshot black list (regex) for :meth:`snapshot` :meth:`instant`

        Can be set until task is submitted.
        """
        self._update_if_summary()
        return self._snapshot_blacklist

    @snapshot_blacklist.setter
    def snapshot_blacklist(self, value):
        """Setter for snapshot blacklist, this can only be set before tasks submission
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        self._snapshot_blacklist = value

    @property
    def results_whitelist(self):
        """:type: :class:`str`
        :getter: Returns this task's results whitelist
        :setter: Sets this task's results whitelist

        Results whitelist (regex)

        Can be set until task is submitted.
        """
        self._update_if_summary()
        return self._results_whitelist

    @results_whitelist.setter
    def results_whitelist(self, value):
        """Setter for results whitelist, this can only be set before tasks submission
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        self._results_whitelist = value

    @property
    def results_blacklist(self):
        """:type: :class:`str`
        :getter: Returns this task's results blacklist
        :setter: Sets this task's results blacklist

        Results blacklist (regex)

        Can be set until task is submitted.
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._results_blacklist

    @results_blacklist.setter
    def results_blacklist(self, value):
        """Setter for results blacklist, this can only be set before tasks submission
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        self._results_blacklist = value

    @property
    def status(self):
        """:type: :class:`qarnot.status.Status`
        :getter: Returns this task's status

        Status of the task
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        if self._status:
            return Status(self._status)
        return self._status

    @property
    def completed_instances(self):
        """:type: list(:class:`CompletedInstance`)
        :getter: Return this task's completed instances
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()
        return self._completed_instances

    @property
    def creation_date(self):
        """:type: :class:`str`

        :getter: Returns this task's creation date

        Creation date of the task (UTC Time)
        """
        return self._creation_date

    @property
    def errors(self):
        """:type: list(:class:`Error`)
        :getter: Returns this task's errors if any.

        Error reason if any, empty string if none
        """
        self._update_if_summary()
        if self._auto_update:
            self.update()

        return self._errors

    @property
    def constants(self):
        """:type: dictionary{:class:`str` : :class:`str`}
        :getter: Returns this task's constants dictionary.
        :setter: set the task's constants dictionary.

        Update the constants if needed
        Constants are the parametrazer of the profils.
        Use them to adjust your profile parametter.
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
        :getter: Returns this task's constraints dictionary.
        :setter: set the task's constraints dictionary.

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
    def wait_for_pool_resources_synchronization(self):
        """:type: :class:`bool` or None
        :getter: Returns this task's wait_for_pool_resources_synchronization.
        :setter: set the task's wait_for_pool_resources_synchronization.

        :raises qarnot.exceptions.AttributeError: can't set this attribute on a launched task
        """
        return self._wait_for_pool_resources_synchronization

    @wait_for_pool_resources_synchronization.setter
    def wait_for_pool_resources_synchronization(self, value):
        """Setter for wait_for_pool_resources_synchronization
        """
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        self._wait_for_pool_resources_synchronization = value

    @property
    def auto_update(self):
        """:type: :class:`bool`

        :getter: Returns this task's auto update state
        :setter: Sets this task's auto update state

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

        :getter: Returns this task's auto update state
        :setter: Sets this task's auto update state

        Cache expiration time, default to 5s
        """
        return self._update_cache_time

    @update_cache_time.setter
    def update_cache_time(self, value):
        """Setter for update_cache_time
        """
        self._update_cache_time = value

    def set_task_dependencies_from_uuids(self, uuids):
        """Setter for the task dependencies using uuid
        """
        self._dependentOn += uuids

    def set_task_dependencies_from_tasks(self, tasks):
        """Setter for the task dependencies using tasks
        """
        self._dependentOn += [task._uuid for task in tasks]

    @property
    def auto_delete(self):
        """Autodelete this Task if it is finished and your max number of task is reach

        Can be set until :meth:`run` or :meth:`submit` is called.

        :type: :class:`bool`
        :getter: Returns is this task must autodelete
        :setter: Sets this task's autodelete
        :default_value: "False"

        :raises AttributeError: if you try to reset the auto_delete after the task is submit
        """
        self._update_if_summary()
        return self._auto_delete

    @auto_delete.setter
    def auto_delete(self, value):
        """Setter for auto_delete, this can only be set before tasks submission
        """
        self._update_if_summary()
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        self._auto_delete = value

    @property
    def completion_ttl(self):
        """The task will be auto delete `completion_ttl` after it is finished

        Can be set until :meth:`run` or :meth:`submit` is called.

        :getter:  Returns this task's completed time to live.
        :type: :class:`str`
        :setter: Sets this task's this task's completed time to live.
        :type: :class:`str` or :class:`datetime.timedelta`
        :default_value: ""

        :raises AttributeError: if you try to set it after the task is submitted

        The `completion_ttl` must be a timedelta or a time span format string (example: 'd.hh:mm:ss' or 'hh:mm:ss')
        """
        self._update_if_summary()
        return self._completion_time_to_live

    @completion_ttl.setter
    def completion_ttl(self, value):
        """Setter for completion_ttl, this can only be set before tasks submission"""
        self._update_if_summary()
        if self._uuid is not None:
            raise AttributeError("can't set attribute on a submitted job")
        self._completion_time_to_live = _util.parse_to_timespan_string(value)

    def _to_json(self):
        """Get a dict ready to be json packed from this task."""
        const_list = [
            {'key': key, 'value': value}
            for key, value in self._constants.items()
        ]
        constr_list = [
            {'key': key, 'value': value}
            for key, value in self._constraints.items()
        ]

        json_task = {
            'name': self._name,
            'profile': self._profile,
            'poolUuid': self._pool_uuid,
            'jobUuid': None if self._job_uuid == "" else self._job_uuid,
            'constants': const_list,
            'constraints': constr_list,
            'dependencies': {},
            'waitForPoolResourcesSynchronization': self._wait_for_pool_resources_synchronization
        }
        json_task['dependencies']["dependsOn"] = self._dependentOn

        if self._shortname is not None:
            json_task['shortname'] = self._shortname

        self._resource_object_ids = [x.uuid for x in self._resource_objects]
        json_task['resourceBuckets'] = self._resource_object_ids

        if self._result_object is not None:
            json_task['resultBucket'] = self._result_object.uuid

        if self._advanced_range is not None:
            json_task['advancedRanges'] = self._advanced_range
        else:
            json_task['instanceCount'] = self._instancecount

        json_task["tags"] = self._tags

        if self._snapshot_whitelist is not None:
            json_task['snapshotWhitelist'] = self._snapshot_whitelist
        if self._snapshot_blacklist is not None:
            json_task['snapshotBlacklist'] = self._snapshot_blacklist
        if self._results_whitelist is not None:
            json_task['resultsWhitelist'] = self._results_whitelist
        if self._results_blacklist is not None:
            json_task['resultsBlacklist'] = self._results_blacklist

        json_task['autoDeleteOnCompletion'] = self._auto_delete
        json_task['completionTimeToLive'] = self._completion_time_to_live
        return json_task

    def _update_if_summary(self):
        """Trigger flush update if the task is made from a summary.

        This should be called before accessing any fields not contained in a summary task
        """
        if self._is_summary:
            self.update(True)

    def __repr__(self):
        return '{0} - {1} - {2} - {3} - InstanceCount : {4} - {5} - Resources : {6} - Results : {7}'\
            .format(self.name,
                    self.shortname,
                    self._uuid,
                    self._profile,
                    self._instancecount,
                    self.state,
                    (self._resource_object_ids if self._resource_objects is not None else ""),
                    (self._result_object.uuid if self._result_object is not None else ""))

    # Context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if (exc_type is None) or exc_type != MissingTaskException:
            self.delete()
        return False


class CompletedInstance(object):
    """Completed Instance Information

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.instance_id = json['instanceId']
        """:type: :class:`int`

        Instance number."""

        self.state = json['state']
        """:type: :class:`str`

        Instance final state."""

        self.wall_time_sec = json['wallTimeSec']
        """:type: :class:`float`

        Instance wall time in seconds."""

        self.exec_time_sec = json['execTimeSec']
        """:type: :class:`float`

        Execution time in seconds."""

        self.exec_time_sec_ghz = json['execTimeSecGHz']
        """:type: :class:`float`

        Execution time in seconds GHz."""

        self.peak_memory_mb = json['peakMemoryMB']
        """:type: :class:`int`

        Peak memory size in MB."""

        self.average_ghz = json['averageGHz']
        """:type: :class:`float`

        Instance execution time GHz"""

        self.results = json['results']
        """:type: :class:list(`str`)

          Instance produced results"""

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member


class BulkTaskResponse(object):
    """Bulk Task Response Information

    .. note:: Read-only class
    """
    def __init__(self, json):
        self.status_code = json['statusCode']
        """:type: :class:`int`

        Status code."""

        self.uuid = json['uuid']
        """:type: :class:`str`

        Created Task Uuid."""

        self.message = json['message']
        """:type: :class:`str`

        User friendly error message."""

    def is_success(self):
        """Check that the task submit has been successful.

        :rtype: :class:`bool`
        :returns: The task creation success(depending on received uuid and the status code).
        """
        return self.status_code >= 200 and self.status_code < 300 and self.uuid

    def __repr__(self):
        if sys.version_info > (3, 0):
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.items())
        else:
            return ', '.join("{0}={1}".format(key, val) for (key, val) in self.__dict__.iteritems())  # pylint: disable=no-member
