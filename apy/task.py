"""module to handle a Task"""

import disk

class QTask(object):
    def __init__(self, connection, name, profile, frameNbr):
        self.name = name
        self.profile = profile
        self.frameCount = frameNbr
        self.priority = 0
        self._resourceDisk = None
        self._resultDisk = None
        self._connction = connection
        self.constants = {}
        self.status = 'UnSubmitted'
        self.uuid = None


    @classmethod
    def retreive(cls, connection, uuid):
        """retreive a submited task given it's uuid"""
        resp = connection.get(get_url('task update', uuid=uuid))
        #check ret code
        t = QTask(connection, "stub", None, 0)
        t._update(resp.json())
        return t

    def submit(self):
        pass #change into json object and send

    def abort(self):
        pass

    def update(self):
        """get the current state of this task and return it's status"""
        if self.status == 'UnSubmitted':
            return self.status

    def _update(self, jsonTask):
        self.name = jsonTask['name']
        self.profile = jsonTask['profile']
        self.framecount = jsonTask['numberOfFrame']
        self._resourceDisk = disk.QDisk.retreive(
            jsonTask['resourceDisk'])
        #question : what to do upon change of disk
        self._resultDisk = disk.QDisk.retreive(jsonTask['resultDisk'])
        self.priority = jsonTask['priority']
        self.uuid = jsonTask['id']

    def wait(self):
        pass

    def status(self):
        pass

    @property
    def resources(self):
        if self._resourceDisk is None:
            disk = disk.QDisk.create(self._connection,
                                     "task {}".format(self.name))
            self._resourcedisk = disk
        return self._resourceDisk

    def _to_json(self):
        """get a dictionnary ready to be json serialized from this task"""
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]

        jsonTask = {
            'name': self.name,
            'profile': self.profile,
            'numberOfFrame': self.frameCount,
            'resourceDisk': self._ressourcedisk.name,
            'constant': const_list
        }
        return jsonTask
