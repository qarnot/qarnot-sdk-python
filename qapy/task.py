"""Module to handle a task."""

import qapy.disk as disk
from qapy import get_url
import time
import warnings
import os.path as path
import os

class QTask(object):
    """Represents a Qarnot job.

    .. note::
       A :class:`QTask` must be created with :meth:`qapy.connection.QApy.create_task`
       or retrieved with :meth:`qapy.connection.QApy.tasks`.
    """
    def __init__(self, connection, name, profile, frameNbr):
        """Create a new :class:`QTask`.

        :param connection: the cluster on which to send the task
        :type connection: :class:`Qconnection`
        :param name: given name of the task
        :type name: :class:`string`
        :param profile: which profile to use with this task
        :type profile: :class:`string`
        :param frameNbr: number of frame on which to run task
        :type frameNbr: :class:`int`
        """
        self._name = name
        self._profile = profile
        self._framecount = frameNbr
        self._resourceDisk = None
        self._resultDisk = None
        self._connection = connection
        self.constants = {}
        """
        Dictionary [CST] = val.

        Can be set until :meth:`submit` is called

        .. note:: See available constants for a specific profile
              with :meth:`qapy.connection.QApy.profile_info`.
        """

        self._status = 'UnSubmitted' # RO property same for below
        self._uuid = None
        self._snapshots = False
        self._resdir = None
        self._dirty = False
        self._rescount = -1
        self._advanced_range = None

    @classmethod
    def _retrieve(cls, connection, uuid):
        """Retrieve a submitted task given its uuid.

        :param qapy.connection.QConnection connection:
          the cluster to retrieve the task from
        :param str uuid: the uuid of the task to retrieve

        :rtype: QTask
        :returns: The retrieved task.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: no such task
        """
        resp = connection._get(get_url('task update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], uuid)
        resp.raise_for_status()
        task = cls(connection, "stub", None, 0)
        task._update(resp.json())
        return task

    def submit(self, resdir, force=False, job_timeout=None):
        """Submit task, wait for the results and download them.

        :param str resdir: path to a directory that will contain the results
        :param bool force: remove an old task if the maximum number of allowed
           tasks is reached
        :param float job_timeout: the task will :meth:`abort` if it has not already
           finished

        :rtype: :class:`string`
        :returns: Path to the directory containing the results (may be None).

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: Will ensure all added file are on the resource disk
           regardless of their uploading mode.
        .. note:: If this function is interrupted (script killed for example),
           but the task is submitted, the task will still be executed remotely
           (results will not be downloaded)
        .. warning:: Will override *resdir* content.
        """
        self.submit_async(resdir, force)
        self.wait(timeout=job_timeout)
        if job_timeout is not None:
            self.abort()
        return self.results()

    def resume(self, resdir):
        """Resume waiting for this task if it is still in submitted mode.
        Equivalent to :meth:`wait` + :meth:`results`.

        :param str resdir: path to a directory that will contain the results

        :rtype: :class:`string`
        :returns: Path to the directory containing the results (may be None).

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not exist
        :raises qapy.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: Do nothing if the task has not been submitted.
        .. warning:: Will override *resdir* content.
        """
        self._resdir = resdir
        if self._uuid is None:
            return resdir
        self.wait()
        return self.results()

    def submit_async(self, resdir, force=False):
        """Submit task to the cluster if it is not already submitted.

        :param str resdir: path to a directory that will contain the results
        :param bool force: delete an old task (and its disks)
          if maximum number of tasks is reached

        :rtype: :class:`string`
        :returns: Status of the task (see :attr:`status`)

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: Will ensure all added file are on the resource disk
           regardless of their uploading mode.

        .. note:: To get the results, call :meth:`results` once the job is done.
        """
        url = get_url('task force') if force else get_url('tasks')
        if self._uuid is not None:
            return self._status
        self.resources.sync()
        payload = self._to_json()
        resp = self._connection._post(url, json=payload)

        if resp.status_code == 404:
            msg = self._resourceDisk.name
            self._resourceDisk = None
            raise disk.MissingDiskException(msg)
        elif resp.status_code == 403:
            raise MaxTaskException(resp.json()['message'])
        else:
            resp.raise_for_status()
        self._uuid = resp.json()['guid']

        if not isinstance(self._snapshots, bool):
            self.snapshot(self._snapshots)

        self._resdir = resdir
        return self.update()

    def resume_async(self, resdir):
        """Download results in *resdir* even if the task is not finished.

        :param str resdir: path to a directory that will contain the results
        :rtype: :class:`str`
        :returns: Path to the directory containing the results (may be None).

        .. warning:: Will override *resdir* content.
        """
        self._resdir = resdir
        return self.results()

    def abort(self):
        """Abort this task if running. Update status to Cancelled.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one

        .. warning:: If this task is already finished, a call to :meth:`abort` will delete it.
        """
        if self._uuid is None or self._status != "Submitted":
            return

        resp = self._connection._delete(
            get_url('task update', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        self.update()

    def delete(self, purge=True):
        """Delete this task on the server. Does nothing if it is already deleted.

        :param bool purge: if True, delete also result and resource disks.
          Defaults to True.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one

        .. note:: *force* parameter in :meth:`submit` and :meth:`submit_async`
           may be set to True in order to delete old tasks automatically.
        """
        if self._uuid is None:
            return
        if self._status == 'Submitted':
            self.abort()


        #change MissingDisk error to warnings,
        #since disks have to be deleted anyway

        if purge and self._resourceDisk:
                try:
                    self._resourceDisk.delete()
                except disk.MissingDiskException as e:
                    warnings.warn(e.message)
                self._resourceDisk = None

        #user can't acess result disk, delete it in any case
        if self._resultDisk:
            try:
                self._resultDisk.delete()
            except disk.MissingDiskException as e:
                warnings.warn(e.message)
            self._resultDisk = None

        resp = self._connection._delete(
            get_url('task update', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        self._uuid = None

    def update(self):
        """Get the current state of this task from the cluster and return
        its status.

        :rtype: :class:`string`
        :returns: Status of the task (see :attr:`status`)

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one
        """
        if self._uuid is None:
            return self._status

        resp = self._connection._get(
            get_url('task update', uuid=self._uuid))
        if resp.status_code == 404:
            return MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()
        self._update(resp.json())

        return self._status

    def _update(self, jsonTask):
        """Update this task from retrieved info."""
        self._name = jsonTask['name']
        self._profile = jsonTask['profile']
        self._framecount = jsonTask.get('frameCount')
        self._advanced_range = jsonTask.get('advancedRanges')

        try:
            self._resourceDisk = disk.QDisk._retrieve(self._connection,
                                                      jsonTask['resourceDisk'])
        except disk.MissingDiskException:
            self._resourceDisk = None

        if jsonTask['resultDisk'] is not None:
            try:
                self._resultDisk = disk.QDisk._retrieve(self._connection,
                                                        jsonTask['resultDisk'])
            except disk.MissingDiskException:
                self._resultDisk = None

        self._uuid = jsonTask['id']
        self._status = jsonTask['state']

        if self._rescount < jsonTask['resultsCount']:
            self._dirty= True
        self._rescount = jsonTask['resultsCount']

    def wait(self, timeout=None):
        """Wait for this task until it is completed.

        :param float timeout: maximum time (in seconds) to wait before returning
           (None => no timeout)

        :rtype: :class:`string`
        :returns: Status of the task (see :attr:`status`)

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one
        """
        start = time.time()
        if self._uuid is None:
            return self.update()

        nap = min(10, timeout) if timeout is not None else 10

        self.update()
        while self._status == 'Submitted':
            time.sleep(nap)
            self.update()

            if timeout is not None:
                elapsed = time.time() - start
                if timeout <= elapsed:
                    return self.update()
                else:
                    nap = min(10, timeout - elapsed)
        return self.update()

    def snapshot(self, interval):
        """Start snapshooting results.
        If called, this task's results will be periodically
        updated, instead of only being available at the end.

        Snapshots will be taken every *interval* second from the time
        the task is submitted.

        :param int interval: the interval in seconds at which to take snapshots

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one

        .. note:: To get the temporary results, call :meth:`results`.
        """
        if self._uuid is None:
            self._snapshots = interval
            return
        resp = self._connection._post(get_url('task snapshot', uuid=self._uuid),
                                      json={"interval" : interval})

        if resp.status_code == 400:
            raise ValueError(interval)
        elif resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        self._snapshots = True

    def instant(self): #change to snapshot and other to snapshot_periodic ?
        """Make a snapshot of the current task.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one

        .. note:: To get the temporary results, call :meth:`results`.
        """
        if self._uuid is None:
            return

        resp = self._connection._post(get_url('task instant', uuid=self._uuid),
                                      json=None)

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        self.update()

    def status(self):
        """:type: :class:`string`

        Current task status.

        Value is in
           * 'UnSubmitted'
           * 'Submitted'
           * 'Cancelled'
           * 'Success'
           * 'Failure'

        Alias of :meth:`update`
        """
        return self.update()

    @property
    def resources(self):
        """:type: :class:`~qapy.disk.QDisk`

        Represents resource files."""
        if self._resourceDisk is None:
            _disk = self._connection.create_disk("task {}".format(self._name))
            self._resourceDisk = _disk

        return self._resourceDisk

    @resources.setter
    def resources(self, value):
        """This is a setter."""
        #question delete current disk ?
        self._resourceDisk = value

    def results(self):
        """Download results in *resdir*.
        *resdir* must have been previously set.

        :rtype: :class:`str`
        :returns: The path containing task results.

        .. warning:: Will override *resdir* (previously provided) content.
        """
        if self._uuid is not None:
            self.update()

        if self._resdir is not None and not path.exists(self._resdir):
            os.makedirs(self._resdir)

        if self._resultDisk is not None and \
           self._resdir is not None and self._dirty :
            for fInfo in self._resultDisk:
                outpath = path.normpath(fInfo.name.lstrip('/'))
                self._resultDisk.get_file(fInfo, path.join(self._resdir,
                                                           outpath))

        return self._resdir

    def stdout(self):
        """Get the standard output of the task
        since the submission of the task.

        :rtype: :class:`str`
        :returns: The standard ouput.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one

        .. note:: The buffer is circular, if stdout is too big, prefer calling
          :meth:`fresh_stdout` regularly.
        """
        if self._uuid is None:
            return ""
        resp = self._connection._get(
            get_url('task stdout', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        return resp.text

    def fresh_stdout(self):
        """Get what has been written on the standard output since last time
        this function was called or since the task has been submitted.

        :rtype: :class:`str`
        :returns: The new output since last call.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one
        """
        if self._uuid is None:
            return ""
        resp = self._connection._post(
            get_url('task stdout', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        return resp.text

    def stderr(self):
        """Get the standard error of the task
        since the submission of the task.

        :rtype: :class:`str`
        :returns: The standard error.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one

        .. note:: The buffer is circular, if stderr is too big, prefer calling
          :meth:`fresh_stderr` regularly.
        """
        if self._uuid is None:
            return ""
        resp = self._connection._get(
            get_url('task stderr', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        return resp.text

    def fresh_stderr(self):
        """Get what has been written on the standard error since last time
        this function was called or since the task has been submitted.

        :rtype: :class:`str`
        :returns: The new error messages since last call.

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.task.MissingTaskException: task does not represent a valid one
        """
        if self._uuid is None:
            return ""
        resp = self._connection._post(
            get_url('task stderr', uuid=self._uuid))

        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], self._name)
        else:
            resp.raise_for_status()

        return resp.text


    @property
    def uuid(self):
        """:type: :class:`string`

        The task's uuid.

        Automatically set when a task is submitted.
        """
        return self._uuid

    @property
    def name(self):
        """:type: :class:`string`

        The task's name.

        Can be set until :meth:`submit` is called
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
    def profile(self):
        """:type: :class:`string`

        The profile to run the task with.

        Can be set until :meth:`submit` is called.
        """
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

        Can be set until :meth:`submit` is called.
        """
        return self._framecount

    @framecount.setter
    def framecount(self, value):
        """Setter for framecount."""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._framecount = value

    @property
    def advanced_range(self):
        """:type: :class:`string`

        Advanced frame range selection.

        Allows to select which frames will be computed.
        Should be None or match the following extended regular expression
        """r"""**"(\\[[0-9]+-[0-9]+\\])( \\[[0-9]+-[0-9]+\\])*"**

        This parameter will override :attr:`framecount`.
        *[min-max]* will generate (max - min) frames from min to max (excluded).

        Can be set until :meth:`submit` is called.
        """
        return self._advanced_range

    @advanced_range.setter
    def advanced_range(self, value):
        """Setter for advanced_range."""
        self._advanced_range = value


    def _to_json(self):
        """Get a dict ready to be json packed from this task."""
        self.resources #init resource_disk if not done
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]

        jsonTask = {
            'name': self._name,
            'profile': self._profile,
            'resourceDisk': self._resourceDisk.name,
            'constants': const_list
        }
        if self._advanced_range is not None:
            jsonTask['advancedRanges'] = self._advanced_range
        else:
            jsonTask['frameCount'] = self._framecount
        return jsonTask

    #context manager#

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if (exc_type is None) or exc_type != MissingTaskException:
            self.delete()
        return False


##############
# Exceptions #
##############

class MissingTaskException(Exception):
    """Non existant task."""
    def __init__(self, message, name):
        super(MissingTaskException, self).__init__(
            "{}: {}".format(message, name))

class MaxTaskException(Exception):
    """Max number of tasks reached."""
    pass
