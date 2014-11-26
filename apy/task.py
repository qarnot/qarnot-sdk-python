"""module to handle a Task"""

import disk
from apy import get_url

class QTask(object):
    def __init__(self, connection, name, profile, frameNbr):
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
        """retreive a submited task given it's uuid"""
        resp = connection.get(get_url('task update', uuid=uuid))
        resp.raise_for_status()#404 is a trivial error here
        t = QTask(connection, "stub", None, 0)
        t._update(resp.json())
        return t

    def submit(self):
        payload = self._to_json()
        resp = self._connection.post(get_url('tasks'), json=payload)

        if resp.status_code == 404:
            raise disk.MissingDiskException(self._resourceDisk.name)
        elif resp.status_code == 403:
            return None#replace by appropriate
        else:
            resp.raise_for_status()

        self.uuid = resp.json()['guid']
        self.update()

        return resp

    def abort(self):
        pass

    def update(self):
        """get the current state of this task and return it's status"""
        if self.uuid is None:
            return self.status

        resp = self._connection.get(
            get_url('task update', uuid=self.uuid))
        if resp.status_code == 404:
            return None #raise task not found
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
        pass

    def snapshot(self):
        pass

    @property
    def resources(self):
        if self._resourceDisk is None:
            _disk = disk.QDisk.create(self._connection,
                                      "task {}".format(self.name))
            self._resourceDisk = _disk

        return self._resourceDisk

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
            'constant': const_list
        }
        return jsonTask
