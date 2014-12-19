"""module to handle a Task"""

import qapy.disk as disk
from qapy import get_url
import time
import warnings

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
        t = cls(connection, "stub", None, 0)
        t._update(resp.json())
        t._resourceDir = disk.QDir(t._resourceDisk)
        return t

    def submit(self):
        """submit task to the cluster if not already submitted

        :rtype: string
        :returns: the current state of the task

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises qapy.disk.MissingDiskException:
          resource disk is not a valid disk
        """
        if self._uuid is not None:
            return self._status
        self.resources.sync()
        payload = self._to_json()
        resp = self._connection._post(get_url('tasks'), json=payload)

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

        return self.update()

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

        if purge:
            if self._resourceDisk:
                try:
                    self._resourceDisk.delete()
                except disk.MissingDiskException as e:
                    warnings.warn(e.message)
                self._resourceDisk = None
            if self._resultDisk:
                try :
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

        self.priority = jsonTask['priority']
        self._uuid = jsonTask['id']
        self._status = jsonTask['state']

    def wait(self):
        """wait for this task to complete

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises MissingTaskException: task does not represent a valid one
        """
        if self._uuid is None:
            return
        self.update()
        while self._status == 'Submitted':
            time.sleep(10)
            self.update()

    def snapshot(self, interval):
        """start snapshooting results
        if called, this task's results will be periodically
        updated, instead of only being available at the end.

        the snapshots will be taken every *interval* second from the time
        the task is submitted

        .. note:: this alters the behavior of results making its access
           non blocking

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

    @property
    def status(self):
        """current task status,
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
        #question delete current disk ?
        self._resourceDisk = value

    @property
    def results(self):
        """:class:`~qapy.disk.QDisk` for task results,
        will wait for the task to end unless snapshot has been called,
        requires the task to :meth:`update`
        """
        if self._uuid is not None:
            if self._snapshots is not True:
                self.wait()
            else:
                self.update()

        return self._resultDisk

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


    @property
    def stderr(self):
        """get the standard error of the task
        each call will return the standard error
        since the submission of the task,

        .. note:: This is *Not* the standard error from the payload
           it is the output for task level errors

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
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._profile = value

    @property
    def framecount(self):
        """number of frames neede for the task

        can be set until :meth:`submit` is called
        """
        return self._framecount

    @framecount.setter
    def framecount(self, value):
        if self.uuid is not None:
            raise AttributeError("can't set attribute on a launched task")
        else:
            self._profile = value


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
