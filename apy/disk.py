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

        jsondisk : dict representing the disk,
          must contain following keys :
            id : string, the disk's UUID
            description : string, a short description of the disk
            nbFiles : integer, number of files on the disk
            readOnly : boolean, is the disk read only
        connection : Qconnection, the qnode on which the disk isw
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

        Raises:
        HTTPError: unhandled http return code
        UnauthorizedException : invalid credentials
        """
        data = {
            "description" : description
            }
        response = connection.post(get_url('disk folder'), json=data)

        if response.status_code != 200: #raise unexpected status code
            response.raise_for_status()

        disk_id = response.json()
        return cls.retrieve(connection, disk_id['guid'])


    @classmethod
    def retrieve(cls, connection, disk_id):
        """retrieve information of a disk on a qnode

        Parameters :
          connection : QConnection, represents the qnode
            to get the disk from
          disk_id : the UUID of the disk to retrieve

        Return value : QDisk
        Qdisk corresponding to the retrieved info

        Raises:
        MissingDiskException : the disk is not on the server
        HTTPError: unhandled http return code
        UnauthorizedException: invalid credentials
        """
        response = connection.get(get_url('disk info', name=disk_id))

        if response.status_code == 404:
            raise MissingDiskException(disk_id)
        elif response.status_code != 200:
            response.raise_for_status()

        return QDisk(response.json(), connection)

    #Disk Manangment#

    def delete(self):
        """delete the disk represented by this Qdisk

        Return value:bool
        whether or not deletion was successful

        Raises :
        MissingDiskException: the disk is not on the server
        UnauthorizedException: invalid credentials
        HTTPError: unhandled http return code
        """
        response = self._connection.delete(
            get_url('disk info', name=self.name))

        if (response.status_code == 404):
            raise MissingDiskException(self.name)

        response.raise_for_status()

        return response.status_code == 200

    def get_archive(self, extension, output=None):
        """retrieve an archive of this disk's content

        Parameters:

        extension : in {'tar', 'tgz', 'zip'},
          format of the archive to get
        output : string, name of the file to output to

        Return value :
         the filename of the retrieved archive

        Raises :

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
        """list files on the disk as FileInfo named Tuples

        Return: list of FileInfo
        list of the files on the disk

        Raises:
        MissingDiskException: this disk doesn't represent a remote one
        HTTPError: unhandled http return code
        UnauthorizedException: invalid credentials
        """
        response = self._connection.get(
            get_url('ls disk', name=self.name))
        if (response.status_code == 404):
            raise MissingDiskException(self.name)
        elif response.status_code != 200:
            response.raise_for_status()
        return [FileInfo._make(f.values()) for f in response.json()]

    def add_file(self, filename, dest=None):
        """add a file to the disk (<=> self[dest] = filename)

        Parameters:
        filename: string, name of the local file file
        dest: string, name of the remote file
          (defaults to filename)

        Return : bool
        whether the file has been successfully added

        Raises:
        ValueError: trying to write on a R/O disk
        UnauthorizedException: invalid credentials
        MissingDiskException: this disk doesn't represent a valid disk
        HTTPError: unhandled http return code
        IOError : user space quota reached
        """

        if self.readonly:
            raise ValueError("tried to write on Read only disk")

        dest = dest or filename

        if isinstance(dest, FileInfo):
            dest = dest.name

        with open(filename) as f:
            response = self._connection.post(
                get_url('update file', name=self.name, path=""),
                files={'filedata': (path.basename(dest),f)})

            if (response.status_code == 404):
                raise MissingDiskException(self.name)
            elif response.status_code == 403:
                raise IOError("disk full")
            else:
                response.raise_for_status()
            return response.status_code == 200


    def get_file(self, filename, outputfile = None):
        """get a file from the disk, you can also use disk['file']

        Parameters:
        filename: string, the name of the remote file
        outputfile: string, local name of retrived file
          (defaults to filename)

        Return:
        the name of the output file

        Raises:
        ValueError : no such file
          (KeyError with disk['file']) syntax
        MissingDiskException: this disk doesn't represent a remote one
        HTTPError: unhandled http return code
        UnauthorizedException: invalid credentials
        """

        if isinstance(filename , FileInfo):
            filename = filename.name

        filename = filename.lstrip('/')

        if outputfile is None:
            outputfile = filename

        response = self._connection.get(
            get_url('update file', name=self.name, path=filename),
            stream=True)

        if response.status_code == 404:
            if response.json()['errorMessage'] != "No such disk":
                raise ValueError('unknown file {}'.format(filename))
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
        """delete a file from the disk, equivalent to del disk['file']

        Parameters:
        filename: string, the name of the remote file

        Return:
        whether or not the deletion was successful (bool)

        Raises:
        ValueError : no such file
          (KeyError with disk['file']) syntax
        MissingDiskException: this disk doesn't represent a remote one
        HTTPError: unhandled http return code
        UnauthorizedException: invalid credentials
        """
        if isinstance(filename , FileInfo):
            filename = filename.name

        response = self._connection.delete(
            get_url('update file', name=self.name, path=filename))

        if response.status_code == 404:
            if response.json()['errorMessage'] != "No such disk":
                raise ValueError('unknown file {}'.format(filename))
            else:
                print response.json()
                raise MissingDiskException(self.name)
        else:
            response.raise_for_status() #raise nothing if 2XX

        return response.status_code == 200

    #operators#

    def __getitem__(self, filename):
        try:
            return self.get_file(filename)
        except ValueError:#change error into keyerror if missing file
            raise KeyError(filename)

    def __setitem__(self, dest, filename):
        return self.add_file(filename, dest)

    def __delitem__(self, filename):
        try:
            return self.delete_file(filename)
        except ValueError: #change error into keyerror if missing file
            raise KeyError(filename)


###################
# Utility Classes #
###################

FileInfo = collections.namedtuple('FileInfo',
                                  ['creation_date', 'name', 'size'])
#"""Named tuple containing the informations on a file"""

class QDir(object):
    """Class for handling files in a disk"""
    def __init__(self, disk):
        self._disk = disk

    def __getitem__(self, filename):
        return self._disk.__getitem__(filename)

    def __setitem__(self, target, filename):
        return self._disk.__setitem__(target, filename)

    def __delitem__(self, filename):
        return self._disk.__delitem__(target, filename)

    def __getattribute__(self, name):
        if name in {'add_file', 'delete_file', 'get_file',
                    'list_files' }:
            return getattr(self._disk, name)
        else:
            return super(QDir, self).__getattribute__(name)

##############
# Exceptions #
##############

class MissingDiskException(Exception):
    """Non existant disk"""
    def __init__(self, name):
        super(MissingDiskException, self).__init__(
            "Disk {} does not exist or has been deleted".format(name))
