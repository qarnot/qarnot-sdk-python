"""module to handle a Task"""

import qapy.disk as disk
from qapy import get_url
import time
import warnings
import os.path as path
import os

class QTask(object):
    """class to represent a qarnot job"""
    def __init__(self, connection, name, profile, frameNbr):
        """create a new :class:`QTask`

        :param connection: :class:`Qconnection`,
          the cluster on which to send the task
        :param name: :class:`string`, given name of the task
        :param profile: :class:`string`, which profile to use with this task
        :param frameNbr: :class:`int`, number of frame on which to run task
        """
        self._name = name
        self._profile = profile
        self._framecount = frameNbr
        self._resourceDisk = None
        self._resultDisk = None
        self._connection = connection
        self.constants = {}
        self._status = 'UnSubmitted' # RO property same for below
        self._uuid = None
        self._snapshots = False
        self._resdir = None
        self._dirty = False
        self._rescount = -1
        self._advanced_range = None

    @classmethod
    def _retrieve(cls, connection, uuid):
        """retrieve a submited task given its uuid

        :param qapy.connection.QConnection connection:
          the cluster to retrieve the task from
        :param str uuid: the uuid of the task to retrieve

        :rtype: Qtask
        :returns: the retrieved task

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: no such task
        """
        resp = connection._get(get_url('task update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingTaskException(resp.json()['message'], uuid)
        resp.raise_for_status()
        task = cls(connection, "stub", None, 0)
        task._update(resp.json())
        return task

    def submit(self, resdir, force=False, job_timeout=None):
        """submit task wait for results and download them

        :param str resdir: path to a directory that will contain the results
        :param bool force: whether to remove old tasks
          if reaching maximum number of allowed tasks
        :param float job_timeout: delay after which abort the task
          if it has not yet finished

        :rtype: string
        :returns: path to the directory now containing the results

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: will ensure all added file are on the ressource disk
           regardless of their uploading mode
        """
        self.submit_async(resdir, force)
        self.wait(timeout=job_timeout)
        if job_timeout is not None:
            self.abort()
        return self.results()

    def resume(self, resdir):
        """resume waiting for a submitted task

        :param str resdir: path to a directory that will contain the results

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.disk.MissingTaskException: task does not exist
        """
        self._resdir = resdir
        if self._uuid is None:
            return resdir
        self.wait()
        return self.results()

    def submit_async(self, resdir, force=False):
        """submit task to the cluster if not already submitted

        :rtype: string
        :returns: the current state of the task

        :param bool force: whether to remove old tasks
          if reaching maximum number of allowed tasks

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.disk.MissingDiskException:
          resource disk is not a valid disk

        .. note:: will ensure all added file are on the ressource disk
           regardless of their uploading mode

        .. note:: To recover results, call :meth:`results`
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
        """resume watching over a task

        :param str resdir: the directory to put results in
        :rtype: str
        :returns: path to directory, now containing the results
        """
        self._resdir = resdir
        return self.results()

    def abort(self):
        """abort this task if running

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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
        """delete task from the server,
        does nothing if already deleted

        :param bool purge: *optional*, if true
          delete also result and ressource disks
          Defaults to True

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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
        """get the current state of this task and return its status

        :rtype: string
        :returns: current status of the task

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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
        """update this task from retrieved info"""
        self._name = jsonTask['name']
        self._profile = jsonTask['profile']
        self._framecount = jsonTask['frameCount']

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
        """wait for this task to complete

        :param float timeout: maximum time to wait before returning in seconds
          (optionnal)

        :rtype: string
        :rvalue: Status of the task (see :attr:`status`)

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
        """
        start = time.time()
        if self._uuid is None:
            return self.status

        nap = min(10, timeout) if timeout is not None else 10

        self.update()
        while self._status == 'Submitted':
            time.sleep(nap)
            self.update()

            if timeout is not None:
                elapsed = time.time() - start
                if timeout <= elapsed:
                    return self.status
                else:
                    nap = min(10, timeout - elapsed)
        return self.status

    def snapshot(self, interval):
        """start snapshooting results
        if called, this task's results will be periodically
        updated, instead of only being available at the end.

        the snapshots will be taken every *interval* second from the time
        the task is submitted

        :param interval: the interval in seconds at which to take snapshots

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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
        """make a snapshot of the current task

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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

    @property
    def status(self):
        """current task status,

        Value is in {'UnSubmitted', 'Submitted', 'Cancelled',
        'Success', 'Failure'}
        requires the task to :meth:`update`
        """
        return self.update()

    @property
    def resources(self):
        """:class:`~qapy.disk.QDisk` for resource files"""
        if self._resourceDisk is None:
            _disk = self._connection.create_disk("task {}".format(self._name))
            self._resourceDisk = _disk

        return self._resourceDisk

    @resources.setter
    def resources(self, value):
        """this is a setter"""
        #question delete current disk ?
        self._resourceDisk = value

    def results(self):
        """path for the directory containing task results,

        requires the task to :meth:`update` in order to get latest results
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

    @property
    def stdout(self):
        """get the standard output of the task,
        each call will return the standard output
        since the submission of the task

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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
        """get what has been written on the standard output since last time
        this function was called or since the task has been submitted

        :rtype: str
        :returns: new output since last call

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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

    @property
    def stderr(self):
        """get the standard error of the task
        each call will return the standard error
        since the submission of the task,

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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
        """get what has been written on the standard error since last time
        this function was called or since the task has been submitted

        :rtype: str
        :returns: new output since last call

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
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
        """the task's uuid"""
        return self._uuid

    @property
    def name(self):
        """given name of the task

        can be set until :meth:`submit` is called
        """
        return self._name

    @name.setter
    def name(self, value):
        """this is a setter docstring is useless"""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._name = value

    @property
    def profile(self):
        """profile to run the task with

        can be set until :meth:`submit` is called
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
        """number of frames needed for the task

        can be set until :meth:`submit` is called
        """
        return self._framecount

    @framecount.setter
    def framecount(self, value):
        """setter for framecount"""
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._framecount = value

    @property
    def advanced_range(self):
        """advanced frame range selection

        allows to select which frames will be computed,
        should be None or match the following extended regular expression
        "'(\[[0-9]+-[0-9]+\] )*'"
        """
        return self._advanced_range

    @advanced_range.setter
    def advanced_range(self, value):
        self._advanced_range = value


    def _to_json(self):
        """get a dict ready to be json packed from this task"""
        self.resources #init ressource_disk if not done
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]

        jsonTask = {
            'name': self._name,
            'profile': self._profile,
            'frameCount': self._framecount,
            'resourceDisk': self._resourceDisk.name,
            'constants': const_list
        }
        if self._advanced_range is not None:
            jsonTask['advancedRanges'] = self._advanced_range
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
    """Non existant task"""
    def __init__(self, message, name):
        super(MissingTaskException, self).__init__(
            "{}: {}".format(message, name))

class MaxTaskException(Exception):
    """max number of tasks reached"""
    pass
