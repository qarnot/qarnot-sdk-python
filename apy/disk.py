"""module for disk object"""

from apy import get_url
import os.path as path
import json

class QDisk(object):
    """represents a ressource disk on the qnode"""
    def __init__(self, jsondisk, connection):
        """
        initialize a disk from a dictionnary.

        Parameters :

        jsondisk : dictionnary representing the disk,
          must contain following keys :
            id : string, the disk's UUID
            description : string, a short description of the disk
            nbFiles : integer, number of files on the disk
            readOnly : boolean, is the disk read only
        connection : Qconnection, the qnode on which the disk is
        """
        self.name = jsondisk["id"]
        self.description = jsondisk["description"]
        self.readonly = jsondisk["readOnly"]
        self._connection = connection

    @classmethod
    def create(cls, connection, description):
        """
        create a disk on a qnode

        Parameters :

        connection : QConnection, represents the qnode
            on which to create the disk
        description : string, a short description of the disk

        Return Value:

        Qdisk corresponding to created disk
        """
        data = {
            "description" : description
            }
        response = connection.post(get_url('disk folder'), json=data)

        if response.status_code != 200:
            return None

        disk_id = response.json()

        disks = connection.disks()

        if disks is None:
            return None

        for disk in disks:
            if disk.name == disk_id:
                return disk
        return None

    def delete(self):
        """delete the disk represented by this Qdisk"""
        response = self._connection.delete(
            get_url('disk remove', name=self.name))

        if (response.status_code == 404):
            raise Exception((404, "No such disk"))

        return response.status_code == 200

    def addFile(self, filename): #TODO finish with api
        """add a file to the disk"""
        with open(filename) as f:
            response = self._connection.post(
                get_url('update file', name=self.name, path=""),
                data = f)

            if (response.status_code == 404):
                raise Exception((404, "No such disk"))
            return response.status_code == 200


    def listFiles(self):
        pass #either cache loacally or use the GET

    def getFile(self, filename):
        """get a file from the disk, you can also use disk['file']"""
        pass

    def __getitem__(self, filename):
        return self.getFile(filename)

    def deleteFile(self, filename):
        pass
