"""module to handle a Task"""

import disk
from apy import get_url
import time

class QTask(object):
    """class to represent a qarnot job"""
    def __init__(self, connection, name, profile, frameNbr):
        """create a new Qtask

        :param connection: :class:`Qconnectionn`,
          the qnode on which to send the task
        :param name: :class:`string`, given name of the task
        :param profile: :class:`string`, which profile to use with this task
        :param frameNbr: :class:`int`, number of frame on which to run task
        """
        self.name = name
        self.profile = profile
        self.frameCount = frameNbr
        self.priority = 0
        self._resourceDisk = None
        self._resourceDir = None
        self._resultDisk = None
        self._resultDir = None
        self._connection = connection
        self.constants = {}
        self.status = 'UnSubmitted'
        self.uuid = None


    @classmethod
    def retrieve(cls, connection, uuid):
        """retrieve a submited task given it's uuid

        :param connection: QConnection, the qnode to retrieve the task from
        :param uuid: string, the uuid of the task to retrieve

        :rtype: Qtask
        :returns: the retrieved task

        :raises:
          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`MissingTaskException`: no such task
        """
        resp = connection.get(get_url('task update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingTaskException(uuid)
        resp.raise_for_status()#replace by missing task
        t = QTask(connection, "stub", None, 0)
        t._update(resp.json())
        return t

    def submit(self):
        """submit task to the qnode if not already submitted

        :rtype: string
        :returns: the current state of the task

        :raises:
          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`apy.disk.MissingDiskException`:
          resource disk is not a valid disk
        """
        if self.uuid is not None:
            return self.status
        self._resourceDir.push()
        payload = self._to_json()
        resp = self._connection.post(get_url('tasks'), json=payload)

        if resp.status_code == 404:
            msg = self._resourceDisk.name
            self._resourceDisk = None
            raise disk.MissingDiskException(msg)
        elif resp.status_code == 403:
            raise MaxTaskException()
        else:
            resp.raise_for_status()

        self.uuid = resp.json()['guid']
        return self.update()

    def abort(self):
        """abort this task if running

        :rtype: bool
        :returns: whether or not task successfully aborted
          will be false if this task is not running

        :raises:
          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`MissingTaskException`: task does not represent a valid one
        """
        if self.uuid is None or self.status != "Submitted":
            return True
        resp = self._connection.delete(
            get_url('task update', uuid=self.uuid))

        if resp.status_code == 404:
            raise MissingTaskException(self.name)
        else:
            resp.raise_for_status()

        self.update()

        return resp.status_code == 200

    def delete(self, purge=True):
        """delete task from the server,
        does nothing if already deleted

        :param purge: :class:`bool` (optional), if true
          delete also result and ressource disks
          Defaults to True

        :rtype: bool
        :returns: whether or not the deletion was successful

        :raises:
          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`MissingTaskException`: task does not represent a valid one
        """
        if self.uuid is None:
            return
        if self.status == 'Submitted':
            self.abort

        if purge:
            if self._resourceDisk:
                self._resourceDisk.delete()
                self._resourceDisk = None
            if self._resultDisk:
                self._resultDisk.delete()
                self._resultDisk = None

        resp = self._connection.delete(
            get_url('task update', uuid=self.uuid))

        if resp.status_code == 404:
            raise MissingTaskException(self.name)
        else:
            resp.raise_for_status()

        self.uuid = None

    def update(self):
        """get the current state of this task and return it's status

        :rtype: string
        :returns: current status of the task

        :raises:
          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`MissingTaskException`: task does not represent a valid one
        """
        if self.uuid is None:
            return self.status

        resp = self._connection.get(
            get_url('task update', uuid=self.uuid))
        if resp.status_code == 404:
            return MissingTaskException(self.name)
        else:
            resp.raise_for_status()
        self._update(resp.json())

        return self.status

    def _update(self, jsonTask):
        """update this task from retrieved info"""
        self.name = jsonTask['name']
        self.profile = jsonTask['profile']
        self.framecount = jsonTask['frameCount']
        self._resourceDisk = disk.QDisk.retrieve(self._connection,
            jsonTask['resourceDisk'])
        #question : what to do upon change of disk
        if jsonTask['resultDisk'] is not None:
            self._resultDisk = disk.QDisk.retrieve(self._connection,
                                               jsonTask['resultDisk'])
        self.priority = jsonTask['priority']
        self.uuid = jsonTask['id']
        self.status = jsonTask['state']

    def wait(self):
        """wait for this task to complete

        :raises:
          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`MissingTaskException`: task does not represent a valid one
        """
        self.update()
        while self.status == 'Submitted':
            time.sleep(10)
            self.update()

    def snapshot(self):#yet undocumented on rest api
        return NotImplemented

    @property
    def resources(self):
        """Qdir for resource files"""
        if self._resourceDisk is None:
            _disk = disk.QDisk.create(self._connection,
                                      "task {}".format(self.name))
            self._resourceDisk = _disk
            self._resourceDir = disk.QDir(_disk)

        return self._resourceDir

    @property
    def results(self):
        """Qdir for task results"""
        if self.uuid is not None: #wait for result when needed
            self.wait()
        if self._resultDir is None:
            self._resultDir = disk.QDir(self._resultDisk)
        return self._resultDir

    def _to_json(self):
        """get a dictionnary ready to be json packed from this task"""
        self.resources #init ressource_disk if not done
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]

        jsonTask = {
            'name': self.name,
            'profile': self.profile,
            'frameCount': self.frameCount,
            'resourceDisk': self._resourceDisk.name,
            'constants': const_list
        }
        return jsonTask


##############
# Exceptions #
##############

class MissingTaskException(Exception):
    """Non existant task"""
    def __init__(self, name):
        super(MissingTaskException, self).__init__(
            "No such task : {}".format(name))

class MaxTaskException(Exception):
    """max number of tasks reached"""
    def __init__(self):
        super(MaxTaskException, self).__init__(
            "max number of running tasks reached")
