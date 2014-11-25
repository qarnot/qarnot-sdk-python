"""module to handle a Task"""

import disk

class QTask(object):
    def __init__(self, connection, name, profile, frameNbr):
        self.name = name
        self.profile = profile
        self.frameCount = frameNbr
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
        pass

    def wait(self):
        pass

    def status(self):
        pass

    @property
    def resources(self):
        return self._resourceDisk

    def _to_json(self):
        pass #to json object
