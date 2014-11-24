"""module to handle a Task"""

class QTask(object):
    def __init__(self, name, profile, frameNbr):
        self.__name__ = name
        self.profile = profile
        self.frameCount = frameNbr
        self.resourceDisk = None #disk object
        self.constants = {}
        self.status = 'UnSubmitted'

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

    def _toJson(self):
        pass #to json object
