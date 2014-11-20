"""module to handle a Task"""

class QTask(object):
    def __init__(self, name, profile, frameNbr):
        self.__name__ = name
        self.profile = profile
        self.frameCount = frameNbr
        self.resourceDisk = None #disk object
        self.constant = {}
        self.submitted = False

    def __del__(self):
        self.abort()

    def submit(self):
        self.submitted = True #change into json object and send

    def abort(self):
        pass

    def wait(self):
        pass

    def status(self):
        pass

    def _toJson(self):
        pass #to json object
