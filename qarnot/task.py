"""Module to handle a task."""

from os import makedirs, path
import time
import datetime
import warnings
import sys

from qarnot import disk
from qarnot import get_url, raise_on_error
from qarnot.disk import MissingDiskException
try:
    from progressbar import AnimatedMarker, Bar, ETA, Percentage, AdaptiveETA, ProgressBar
except:
    pass

RUNNING_DOWNLOADING_STATES = ['Submitted', 'PartiallyDispatched',
                              'FullyDispatched', 'PartiallyExecuting',
                              'FullyExecuting', 'DownloadingResults']


class Task(object):
    """Represents a Qarnot job.

    .. note::
       A :class:`Task` must be created with
       :meth:`qarnot.connection.QApy.create_task`
       or retrieved with :meth:`qarnot.connection.QApy.tasks` or :meth:`qarnot.connection.QApy.retrieve_task`.
    """
    def __init__(self, connection, name, profile, framecount_or_range, force):
        """Create a new :class:`Task`.

        :param connection: the cluster on which to send the task
        :type connection: :class:`QApy`
        :param name: given name of the task
        :type name: :class:`str`
        :param str profile: which profile (payload) to use with this task

        :param framecount_or_range: number of frame or range on which to run
        task
        :type framecount_or_range: int or str

        :param bool force: remove an old task if the maximum number of allowed
           tasks is reached. Plus, it will delete an old unlocked disk
           if maximum number of disks is reached for resources and results

        """
        self._name = name
        self._profile = profile

        if isinstance(framecount_or_range, int):
            self._framecount = framecount_or_range
            self._advanced_range = None
        else:
            self._advanced_range = framecount_or_range
            self._framecount = 0

        self._force = force
        self._resource_disks = []
        self._result_disk = None
        self._connection = connection
        self.constants = {}
        self._auto_update = True
        self._update_cache_time = 5

        self._last_cache = time.time()
        """
        Dictionary [CST] = val.

        Can be set until :meth:`run` is called

        .. note:: See available constants for a specific profile
              with :meth:`qarnot.connection.QApy.profile_info`.
        """

        self.constraints = {}
        self._state = 'UnSubmitted'  # RO property same for below
        self._uuid = None
        self._snapshots = False
        self._dirty = False
        self._rescount = -1
        self._snapshot_whitelist = None
        self._snapshot_blacklist = None
        self._results_whitelist = None
        self._results_blacklist = None
        self._execution_cluster = {}
        self._status = None
        self._creation_date = None
        self._error_reason = None
        self._resource_disks_uuids = []
        self._result_disk_uuid = None

    @classmethod
    def _retrieve(cls, connection, uuid):
        """Retrieve a submitted task given its uuid.

        :param qarnot.connection.QApy connection:
          the cluster to retrieve the task from
        :param str uuid: the uuid of the task to retrieve

        :rtype: Task
        :returns: The retrieved task.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: no such task
        """
        resp = connection._get(get_url('task update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], uuid)
        raise_on_error(resp)
        return Task.from_json(connection, resp.json(), False)

    def run(self, output_dir, job_timeout=None, live_progress=False, results_progress=None):
        """Submit a task, wait for the results and download them.

        :param str output_dir: path to a directory that will contain the results
        :param float job_timeout: Number of second before the task :meth:`abort` if it has not
          already finished
        :param bool live_progress: display a live progress
        :param bool|fun(float,float,str) results_progress: can be a callback (read,total,filename) or True to display a progress bar

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: Will ensure all added file are on the resource disk
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
        self.download_results(output_dir, progress=results_progress)

    def resume(self, output_dir, job_timeout=None, live_progress=False, results_progress=None):
        """Resume waiting for this task if it is still in submitted mode.
        Equivalent to :meth:`wait` + :meth:`download_results`.

        :param str output_dir: path to a directory that will contain the results
        :param float job_timeout: Number of second before the task :meth:`abort` if it has not
          already finished
        :param bool live_progress: display a live progress
        :param bool|fun(float,float,str) results_progress: can be a callback (read,total,filename) or True to display a progress bar

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not exist
        :raises qarnot.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: Do nothing if the task has not been submitted.
        .. warning:: Will override *output_dir* content.
        """
        if self._uuid is None:
            return output_dir
        self.wait(timeout=job_timeout, live_progress=live_progress)
        self.download_results(output_dir, progress=results_progress)

    def submit(self):
        """Submit task to the cluster if it is not already submitted.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: Will ensure all added file are on the resource disk
           regardless of their uploading mode.

        .. note:: To get the results, call :meth:`download_results` once the job is done.
        """
        url = get_url('task force') if self._force else get_url('tasks')
        if self._uuid is not None:
            return self._state
        for rdisk in self.resources:
            rdisk.flush()
        payload = self._to_json()
        resp = self._connection._post(url, json=payload)

        if resp.status_code == 404:
            raise disk.MissingDiskException(resp.json()['message'])
        elif resp.status_code == 403:
            raise MaxTaskException(resp.json()['message'])
        raise_on_error(resp)
        self._uuid = resp.json()['uuid']

        if not isinstance(self._snapshots, bool):
            self.snapshot(self._snapshots)

        self.update(True)

    def abort(self):
        """Abort this task if running. Update state to Cancelled.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent
          a valid one

        .. warning:: If this task is already finished, a call to :meth:`abort`
          will delete it.
        """
        self.update(True)
        if self._uuid is None or self._state in ["None", "Cancelled", "Success", "Failure", "DownloadingResults"]:
            return

        resp = self._connection._delete(
            get_url('task update', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        raise_on_error(resp)

        self.update(True)

    def update_resources(self):
        """Update resources for a running task. Be sure to add new resources first.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent
          a valid one
        """

        self.update(True)
        resp = self._connection._patch(
            get_url('task update', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        raise_on_error(resp)

        self.update(True)

    def delete(self, purge_resources=None, purge_results=None):
        """Delete this task on the server. Does nothing if it is already deleted.

        :param bool purge_resources: if None disk will be deleted unless locked,
                otherwise parameter value is used to determine if the disk is also deleted.
                Defaults to None.

        :param bool purge_results: if None disk will be deleted unless locked,
                otherwise parameter value is used to determine if the disk is also deleted.
                Defaults to None.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
          valid one

        .. note:: *force* parameter in :meth:`qarnot.connection.QApy.create_task`
           may be set to True in order to delete old tasks automatically.
        """
        if self._uuid is None:
            return
        if self._status is not None and \
           self._state in ['Submitted', 'PartiallyDispatched', 'FullyDispatched', 'PartiallyExecuting', 'FullyExecuting']:
            self.abort()

        if purge_resources in [None, True]:
            toremove = []

            for rdisk in self.resources:
                try:
                    rdisk.update()
                    if purge_resources is None:
                        purge_resources = not rdisk.locked
                    if purge_resources:
                        rdisk.delete()
                        toremove.append(rdisk)
                except disk.MissingDiskException as exception:
                    warnings.warn(exception.message)
            for tr in toremove:
                self.resources.remove(tr)

        try:
            self.results.update()
            if purge_results is None:
                purge_results = not self._result_disk.locked
            if purge_results:
                self._result_disk.delete()
                self._result_disk = None
                self._result_disk_uuid = None
        except disk.MissingDiskException as exception:
            warnings.warn(exception.message)

        resp = self._connection._delete(
            get_url('task update', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        raise_on_error(resp)

        self._uuid = None

    def update(self, flushcache=False):
        """
        Update the task object from the REST Api.
        The flushcache parameter can be used to force the update, otherwise a cached version of the object
        will be served when accessing properties of the object.
        Some methods will flush the cache, like :meth:`submit`, :meth:`abort`, :meth:`wait` and :meth:`instant`.
        Cache behavior is configurable with :attr:`auto_update` and :attr:`update_cache_time`.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
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
            raise MissingTaskException(resp.json()['message'], self._name)

        raise_on_error(resp)
        self._update(resp.json())
        self._last_cache = time.time()

    def _update(self, json_task):
        """Update this task from retrieved info."""
        self._name = json_task['name']
        self._profile = json_task['profile']
        self._framecount = json_task.get('frameCount')
        self._advanced_range = json_task.get('advancedRanges')
        self._resource_disks_uuids = json_task['resourceDisks']
        if len(self._resource_disks_uuids) != len(self._resource_disks):
            del self._resource_disks[:]
        self._result_disk_uuid = json_task['resultDisk']
        if 'executionCluster' in json_task:
            self._execution_cluster = json_task['executionCluster']
        if 'status' in json_task:
            self._status = json_task['status']
        self._creation_date = datetime.datetime.strptime(json_task['creationDate'], "%Y-%m-%dT%H:%M:%SZ")
        self._error_reason = json_task['errorReason'] if 'errorReason' in json_task else ""

        self._uuid = json_task['uuid']
        self._state = json_task['state']

        if self._rescount < json_task['resultsCount']:
            self._dirty = True
        self._rescount = json_task['resultsCount']

    @classmethod
    def from_json(cls, connection, json_task, force):
        """Create a Task object from a json task.

        :param qarnot.connection.QApy connection: the cluster connection
        :param dict json_task: Dictionary representing the task
        :returns: The created :class:`~qarnot.task.Task`.
        """
        if 'frameCount' in json_task:
            framecount_or_range = json_task['frameCount']
        else:
            framecount_or_range = json_task['advancedRanges']
        new_task = cls(connection,
                       json_task['name'],
                       json_task['profile'],
                       framecount_or_range,
                       force)
        new_task._update(json_task)
        return new_task

    def commit(self):
        """Replicate local changes on the current object instance to the REST API

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        """
        data = self._to_json()
        resp = self._connection._put(get_url('task update', uuid=self._uuid), json=data)

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)

        raise_on_error(resp)

    def wait(self, timeout=None, live_progress=False):
        """Wait for this task until it is completed.

        :param float timeout: maximum time (in seconds) to wait before returning
           (None => no timeout)
        :param bool live_progress: display a live progress

        :rtype: :class:`bool`
        :returns: Is the task finished

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a valid
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
            except Exception as e:
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

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
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
            raise MissingTaskException(resp.json()['message'], self._name)

        raise_on_error(resp)

        self._snapshots = True

    def instant(self):
        """Make a snapshot of the current task.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
          valid one

        .. note:: To get the temporary results, call :meth:`download_results`.
        """
        if self._uuid is None:
            return

        resp = self._connection._post(get_url('task instant', uuid=self._uuid),
                                      json=None)

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        raise_on_error(resp)

        self.update(True)

    @property
    def state(self):
        """:type: :class:`str`

        State of the task.

        Value is in
           * UnSubmitted
           * Submitted
           * PartiallyDispatched
           * FullyDispatched
           * PartiallyExecuting
           * FullyExecuting
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
        """:type: list(:class:`~qarnot.disk.Disk`)

        Represents resource files."""
        if self._auto_update:
            self.update()

        if not self._resource_disks:
            for duuid in self._resource_disks_uuids:
                d = disk.Disk._retrieve(self._connection,
                                        duuid)
                self._resource_disks.append(d)

        return self._resource_disks

    @resources.setter
    def resources(self, value):
        """This is a setter."""
        self._resource_disks = value

    @property
    def results(self):
        """:type: :class:`~qarnot.disk.Disk`

        Represents results files."""
        if self._result_disk is None:
            self._result_disk = disk.Disk._retrieve(self._connection,
                                                    self._result_disk_uuid)

        if self._auto_update:
            self.update()

        return self._result_disk

    def download_results(self, output_dir, progress=None):
        """Download results in given *output_dir*.

        :param str output_dir: local directory for the retrieved files.
        :param bool|fun(float,float,str) progress: can be a callback (read,total,filename)  or True to display a progress bar

        :raises qarnot.disk.MissingDiskException: the disk is not on the server
        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials

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

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
          valid one

        .. note:: The buffer is circular, if stdout is too big, prefer calling
          :meth:`fresh_stdout` regularly.
        """
        if self._uuid is None:
            return ""
        resp = self._connection._get(
            get_url('task stdout', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)

        raise_on_error(resp)

        return resp.text

    def fresh_stdout(self):
        """Get what has been written on the standard output since last time
        this function was called or since the task has been submitted.

        :rtype: :class:`str`
        :returns: The new output since last call.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
          valid one
        """
        if self._uuid is None:
            return ""
        resp = self._connection._post(
            get_url('task stdout', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)

        raise_on_error(resp)
        return resp.text

    def stderr(self):
        """Get the standard error of the task
        since the submission of the task.

        :rtype: :class:`str`
        :returns: The standard error.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
          valid one

        .. note:: The buffer is circular, if stderr is too big, prefer calling
          :meth:`fresh_stderr` regularly.
        """
        if self._uuid is None:
            return ""
        resp = self._connection._get(
            get_url('task stderr', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)

        raise_on_error(resp)
        return resp.text

    def fresh_stderr(self):
        """Get what has been written on the standard error since last time
        this function was called or since the task has been submitted.

        :rtype: :class:`str`
        :returns: The new error messages since last call.

        :raises qarnot.QApyException: API general error, see message for details
        :raises qarnot.connection.UnauthorizedException: invalid credentials
        :raises qarnot.task.MissingTaskException: task does not represent a
          valid one
        """
        if self._uuid is None:
            return ""
        resp = self._connection._post(
            get_url('task stderr', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)

        raise_on_error(resp)
        return resp.text

    @property
    def uuid(self):
        """:type: :class:`str`

        The task's uuid.

        Automatically set when a task is submitted.
        """
        if self._auto_update:
            self.update()

        return self._uuid

    @property
    def name(self):
        """:type: :class:`str`

        The task's name.

        Can be set until :meth:`run` is called
        """
        if self._auto_update:
            self.update()

        return self._name

    @name.setter
    def name(self, value):
        """Setter for name."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._name = value

    @property
    def profile(self):
        """:type: :class:`str`

        The profile to run the task with.

        Can be set until :meth:`run` is called.
        """
        if self._auto_update:
            self.update()

        return self._profile

    @profile.setter
    def profile(self, value):
        """setter for profile"""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._profile = value

    @property
    def framecount(self):
        """:type: :class:`int`

        Number of frames needed for the task.

        Can be set until :meth:`run` is called.

        :raises AttributeError: if :attr:`advanced_range` is not None when setting this property

        .. warning:: This property is mutually exclusive with :attr:`advanced_range`
        """
        if self._auto_update:
            self.update()

        return self._framecount

    @framecount.setter
    def framecount(self, value):
        """Setter for framecount."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")

        if self.advanced_range is not None:
            raise AttributeError("Can't set framecount if advanced_range is not None")
        self._framecount = value

    @property
    def advanced_range(self):
        """:type: :class:`str`

        Advanced frame range selection.

        Allows to select which frames will be computed.
        Should be None or match the following extended regular expression
        """r"""**"(\\[[0-9]+-[0-9]+\\])( \\[[0-9]+-[0-9]+\\])*"**
        *[min-max]* will generate (max - min) frames from min to max (excluded).

        Can be set until :meth:`run` is called.

        :raises AttributeError: if :attr:`framecount` is not 0 when setting this property

        .. warning:: This property is mutually exclusive with :attr:`framecount`
        """
        if self._auto_update:
            self.update()

        return self._advanced_range

    @advanced_range.setter
    def advanced_range(self, value):
        """Setter for advanced_range."""
        if self.framecount != 0:
            raise AttributeError("Can't set advanced_range if framecount is not 0")
        self._advanced_range = value

    @property
    def snapshot_whitelist(self):
        """Snapshot white list
        """
        if self._auto_update:
            self.update()

        return self._snapshot_whitelist

    @snapshot_whitelist.setter
    def snapshot_whitelist(self, value):
        """Setter for snapshot whitelist, this can only be set before tasks submission
        """
        self._snapshot_whitelist = value

    @property
    def snapshot_blacklist(self):
        """Snapshot black list
        """
        if self._auto_update:
            self.update()

        return self._snapshot_blacklist

    @snapshot_blacklist.setter
    def snapshot_blacklist(self, value):
        """Setter for snapshot blacklist, this can only be set before tasks submission
        """
        self._snapshot_blacklist = value

    @property
    def results_whitelist(self):
        """Results whitelist
        """
        if self._auto_update:
            self.update()

        return self._results_whitelist

    @results_whitelist.setter
    def results_whitelist(self, value):
        """Setter for results whitelist, this can only be set before tasks submission
        """
        self._results_whitelist = value

    @property
    def results_blacklist(self):
        """Results blacklist
        """
        if self._auto_update:
            self.update()

        return self._results_blacklist

    @results_blacklist.setter
    def results_blacklist(self, value):
        """Setter for results blacklist, this can only be set before tasks submission
        """
        self._results_blacklist = value

    @property
    def status(self):
        """Status of the task
        """
        if self._auto_update:
            self.update()

        if self._status:
            return TaskStatus(self._status)
        return self._status

    @property
    def creation_date(self):
        """Creation date of the task (UTC Time)
        """
        if self._auto_update:
            self.update()

        return self._creation_date

    @property
    def execution_cluster(self):
        """Various statistics about running task
        """
        if self._auto_update:
            self.update()

        return self._execution_cluster

    @property
    def error_reason(self):
        """Error reason if any, empty string if none
        """
        if self._auto_update:
            self.update()

        return self._error_reason

    @property
    def auto_update(self):
        """Auto update state, default to True
           When auto update is disabled properties will always return cached value
           for the object and a call to :meth:`update` will be required to get latest values from the REST Api.
        """
        return self._auto_update

    @auto_update.setter
    def auto_update(self, value):
        """Setter for auto_update feature
        """
        self._auto_update = value

    @property
    def update_cache_time(self):
        """Cache expiration time, default to 5s
        """
        return self._update_cache_time

    @update_cache_time.setter
    def update_cache_time(self, value):
        """Setter for update_cache_time
        """
        self._update_cache_time = value

    def _to_json(self):
        """Get a dict ready to be json packed from this task."""
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]
        constr_list = [
            {'key': key, 'value': value}
            for key, value in self.constraints.items()
        ]

        self._resource_disks_uuids = [x.uuid for x in self._resource_disks]
        json_task = {
            'name': self._name,
            'profile': self._profile,
            'resourceDisks': self._resource_disks_uuids,
            'constants': const_list,
            'constraints': constr_list
        }

        if self._advanced_range is not None:
            json_task['advancedRanges'] = self._advanced_range
        else:
            json_task['frameCount'] = self._framecount

        if self._snapshot_whitelist is not None:
            json_task['snapshotWhitelist'] = self._snapshot_whitelist
        if self._snapshot_blacklist is not None:
            json_task['snapshotBlacklist'] = self._snapshot_blacklist
        if self._results_whitelist is not None:
            json_task['resultsWhitelist'] = self._results_whitelist
        if self._results_blacklist is not None:
            json_task['resultsBlacklist'] = self._results_blacklist
        return json_task

    def __str__(self):
        return '{0} - {1} - {2} - FrameCount : {3} - {4} - Resources : {5} - Results : {6}'\
            .format(self.name,
                    self._uuid,
                    self._profile,
                    self._framecount,
                    self.state,
                    (self._resource_disks_uuids if self._resource_disks is not None else ""),
                    (self._result_disk.uuid if self._result_disk is not None else ""))

    # Context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if (exc_type is None) or exc_type != MissingTaskException:
            self.delete()
        return False


# Status
class TaskStatus(object):
    """Task status
    """
    def __init__(self, entries):
        self.download_progress = entries['downloadProgress']
        """:type: :class:`float`

        Resources download progress to the instances."""

        self.execution_progress = entries['executionProgress']
        """:type: :class:`float`

        Task execution progress."""

        self.upload_progress = entries['uploadProgress']
        """:type: :class:`float`

        Task results upload progress to the API."""

        self.instance_count = entries['instanceCount']
        """:type: :class:`int`

        Number of running instances."""

        self.download_time = entries['downloadTime']
        """:type: :class:`int`

        Resources download time to the instances in seconds."""

        self.execution_time = entries['executionTime']
        """:type: :class:`int`

        Task execution time in seconds."""

        self.upload_time = entries['uploadTime']
        """:type: :class:`int`

        Task results upload time to the API in seconds"""

        self.succeeded_range = entries['succeededRange']
        """:type: :class:`str`

        Successful frames range."""

        self.executed_range = entries['executedRange']
        """:type: :class:`str`

        Executed frames range."""

        self.failed_range = entries['failedRange']
        """:type: :class:`str`

        Failed frames range."""

        self.error = entries['error'] if 'error' in entries else ""
        """:type: :class:`str`

        Error reason if any."""


##############
# Exceptions #
##############

class MissingTaskException(Exception):
    """Non existent task."""
    def __init__(self, message, name):
        super(MissingTaskException, self).__init__(
            "{0}: {1}".format(message, name))


class MaxTaskException(Exception):
    """Max number of tasks reached."""
    pass
