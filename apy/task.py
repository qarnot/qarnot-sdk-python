"""module to handle a Task"""

import disk
from apy import get_url
import time

class QTask(object):
    """represent a task running or not"""
    def __init__(self, connection, name, profile, frameNbr):
        """create a new Qtask

        Parameters :

        connection: the qnode on which to send the task
        name: string, given name of the task
        profile: which profile to use with this task
        frameNbr: int, number of frame on which to run task
        """
        self.name = name
        self.profile = profile
        self.frameCount = frameNbr
        self.priority = 0
        self._resourceDisk = None
        self._resultDisk = None
        self._connection = connection
        self.constants = {}
        self.status = 'UnSubmitted'
        self.uuid = None


    @classmethod
    def retreive(cls, connection, uuid):
        """retreive a submited task given it's uuid

        Parameter:

        connection: QConnection, the qnode to retreive the task from
        uuid: string, the uuids of the task to retreive
        """
        resp = connection.get(get_url('task update', uuid=uuid))
        resp.raise_for_status()#404 is a trivial error here
        t = QTask(connection, "stub", None, 0)
        t._update(resp.json())
        return t

    def submit(self):
        """submit task to the qnode"""
        if self.uuid is not None:
            return
        payload = self._to_json()
        resp = self._connection.post(get_url('tasks'), json=payload)

        if resp.status_code == 404:
            raise disk.MissingDiskException(self._resourceDisk.name)
        elif resp.status_code == 403:
            raise MaxTaskException()
        else:
            resp.raise_for_status()

        self.uuid = resp.json()['guid']
        return self.update()

    def abort(self):
        """abort this task if running"""
        if self.uuid is None or self.status != "Submitted":
            return
        resp = self._connection.delete(
            get_url('task update', uuid=self.uuid))

        if resp.status_code == 404:
            raise MissingTaskException(self.name)
        else:
            resp.raise_for_status()

        self.update()

        return resp.status_code == 200

    def delete(self, purge=True):
        """delete task from the server

        Paramters :
        purge : bool (optional), if true
          delete also result and ressource disks
          Defaults to True
        """
        if self.uuid is None:
            return
        if self.status == 'Submitted':
            self.abort

        if purge:
            self._resourceDisk.delete()
            self._resourceDisk = None
            self._resultDisk.delete()
            self._resultDisk = None

        resp = self._connection.delete(
            get_url('task update', uuid=self.uuid))

        self.uuid = None

    def update(self):
        """get the current state of this task and return it's status"""
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
        self.name = jsonTask['name']
        self.profile = jsonTask['profile']
        self.framecount = jsonTask['numberOfFrame']
        self._resourceDisk = disk.QDisk.retreive(self._connection,
            jsonTask['resourceDisk'])
        #question : what to do upon change of disk
        if jsonTask['resultDisk'] is not None:
            self._resultDisk = disk.QDisk.retreive(self._connection,
                                               jsonTask['resultDisk'])
        self.priority = jsonTask['priority']
        self.uuid = jsonTask['id']
        self.status = jsonTask['state']

    def wait(self):
        self.update()
        while self.status == 'Submitted':
            time.sleep(10)
            self.update()

    def snapshot(self):#yet undocumented on rest api
        return NotImplemented

    @property
    def resources(self):
        if self._resourceDisk is None:
            _disk = disk.QDisk.create(self._connection,
                                      "task {}".format(self.name))
            self._resourceDisk = _disk

        return self._resourceDisk

    @property
    def results(self):
        if self.uuid is not None: #wait for result when needed
            self.wait()
        return self._resultDisk

    def _to_json(self):
        """get a dictionnary ready to be json serialized from this task"""
        self.resources #init ressource_disk if not done
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]

        jsonTask = {
            'name': self.name,
            'profile': self.profile,
            'numberOfFrame': self.frameCount,
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
