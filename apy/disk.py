"""module for disk object"""

from apy import get_url
import os.path as path
import json
import collections

class QDisk(object):
    """represents a ressource disk on the qnode"""
    #Creation#
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

        if response.status_code != 200: #raise unexpected status code
            return None

        disk_id = response.json()
        return cls.retreive(connection, disk_id['guid'])


    @classmethod
    def retreive(cls, connection, disk_id):
        """retrive information of a disk on a qnode

        Parameters :
          connection : QConnection, represents the qnode
            to get the disk from
          disk_id : the UUID of the disk to retreive

        Return value :
        Qdisk corresponding to the retreived info
        """
        response = connection.get(get_url('disk info', name=disk_id))

        if response.status_code == 404:
            raise MissingDiskException(disk_id)
        elif response.status_code != 200:
            return None

        return QDisk(response.json(), connection)

    #Disk Manangment#

    def delete(self):
        """delete the disk represented by this Qdisk"""
        response = self._connection.delete(
            get_url('disk info', name=self.name))

        if (response.status_code == 404):
            raise MissingDiskException(self.name)

        return response.status_code == 200

    def get_archive(self, extension, output=None):
        """retreive an archive of this disk's content

        Parameters:

        extension : in {'tar', 'tgz', 'zip'},
          format of the archive to get
        output : string, name of the file to output to

        returns :
         the filename of the retreived archive

        raises :

        UnauthorizedException: invalid credentials
        MissingDiskException: this disk doesn't represent a valid disk
        ValueError: invalid extension format
        HTTPError: unhandled http return code
        """
        response = self._connection.get(
            get_url('get disk', name=self.name, ext=extension),
            stream=True)

        if response.status_code == 404:
            raise MissingDiskException(self.name)
        elif response.status_code == 400:
            raise ValueError('invalid file format : {}'.extension)
        else:
            response.raise_for_status()

        output = output or ".".join([self.name, extension])

        with open(output, 'w') as f:
            for elt in response.iter_content():
                f.write(elt)
        return output


    def list_files(self):
        """list files on the disk as FileInfo named Tuples"""
        response = self._connection.get(
            get_url('ls disk', name=self.name))
        if (response.status_code == 404):
            raise MissingDiskException(self.name)
        elif response.status_code != 200:
            response.raise_for_status()
            print response.status_code()
        return [FileInfo._make(f.values()) for f in response.json()]

    def add_file(self, filename, dest=None):
        """add a file to the disk (<=> self[dest] = filename)

        Parameters:
        filename: string, name of the local file file
        dest: string, name of the remote file
          (defaults to filename)
        """
        dest = dest or filename
        with open(filename) as f:
            response = self._connection.post(
                get_url('update file', name=self.name, path=""),
                files={'filedata': (path.basename(dest),f)})

            if (response.status_code == 404):
                raise MissingDiskException(self.name)
            else:
                response.raise_for_status()
            return response.status_code == 200


    def get_file(self, filename, outputfile = None):
        """get a file from the disk, you can also use disk['file']

        Parameters:
        filename: string, the name of the remote file
        outputfile: string, local name o retrived file
          (defaults to filename)

        Return:
        the name of the output file
        """
        if outputfile is None:
            outputfile = filename
        response = self._connection.get(
            get_url('update file', name=self.name, path=filename),
            stream=True)

        if response.status_code == 404:
            if response.json()['errorMessage'] != "No such disk":
                return None #handle file not found
            else:
                print response.json()
                raise MissingDiskException(self.name)
        else:
            response.raise_for_status() #raise nothing if 2XX

        with open(outputfile, 'w') as f:
            for elt in response.iter_content():
                f.write(elt)
        return outputfile

    def delete_file(self, filename):
        response = self._connection.delete(
            get_url('update file', name=self.name, path=filename))

        if response.status_code == 404:
            if response.json()['errorMessage'] != "No such disk":
                return False #handle file not found
            else:
                print response.json()
                raise MissingDiskException(self.name)
        else:
            response.raise_for_status() #raise nothing if 2XX

        return response.status_code == 200

    #operators#

    def __getitem__(self, filename):
        return self.get_file(filename)

    def __setitem__(self, dest, filename):
        return self.add_file(filename, dest)

    def __delitem__(self, filename):
        return self.delete_file(filename)


###################
# Utility Classes #
###################

FileInfo = collections.namedtuple('FileInfo',
                                  ['creation_date', 'name', 'size'])
"""Named tuple containing the informations on a file"""

##############
# Exceptions #
##############

class MissingDiskException(Exception):
    def __init__(self, name):
        super(MissingDiskException, self).__init__(
            "Disk {} does not exist or has been deleted".format(name))
