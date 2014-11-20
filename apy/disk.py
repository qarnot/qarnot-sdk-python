"""module for disk object"""



class QDisk(object):
    def __init__(self, jsondisk):
        self.name = jsondisk["id"]
        self.description = jsondisk["description"]
        self.nbfiles = jsondisk["nbFiles"]
        self.readonly = jsondisk["readOnly"]
        self.date = jsondisk["creationDate"]
        self.used = jsondisk["usedSpaceBytes"]

    @classmethod
    def create(cls, description)
        #create a disk using api

    def add(self, filename):
        pass

    def listFiles(self):
        pass #either cache loacally or use the GET

    def getFile(self, filename):
        pass

    def deleteFile(self, filename):
        pass
