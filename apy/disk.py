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

        :param jsondisk: dict representing the disk,
          must contain following keys :

            * id: string, the disk's UUID

            * description : string, a short description of the disk

            * nbFiles : integer, number of files on the disk

            * readOnly : boolean, is the disk read only

        :param connection:  :class:`apy.connection.QConnection`,
          the qnode on which the disk is
        """
        self.name = jsondisk["id"]
        self.description = jsondisk["description"]
        self.readonly = jsondisk["readOnly"]
        self._connection = connection

    @classmethod
    def create(cls, connection, description):
        """
        create a disk on a qnode

        :param connection:  :class:`apy.connection.QConnection`,
          represents the qnode on which to create the disk
        :param description: :class:`string`, a short description of the disk

        :rtype: :class:`QDisk`
        :returns: the created disk


        :raises: :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials
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

        :param connection: :class:`apy.connection.QConnection`, the qnode
            to get the disk from
        :param disk_id: the UUID of the disk to retrieve

        :rtype: :class:`QDisk`
        :returns: the retrieved disk

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials
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

        :rtype: bool
        :returns: whether or not deletion was successful

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials
        """
        response = self._connection.delete(
            get_url('disk info', name=self.name))

        if (response.status_code == 404):
            raise MissingDiskException(self.name)

        response.raise_for_status()

        return response.status_code == 200

    def get_archive(self, extension, output=None):
        """retrieve an archive of this disk's content

        :param extension: in {'tar', 'tgz', 'zip'},
          format of the archive to get
        :param output: :class:`str`, name of the file to output to

        :rtype: :class:`str`
        :returns:
         the filename of the retrieved archive

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`ValueError`: invalid extension format

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

        :rtype: list of :class:`FileInfo`
        :returns: list of the files on the disk

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials
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

        :param filename: :class:`string`, name of the local file
        :param dest: :class:`string`, name of the remote file
          (defaults to filename)

        :rtype: :class:`bool`
        :returns: whether the file has been successfully added

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`ValueError`: trying to write on a R/O disk

          :exc:`IOError`: user space quota reached
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

        :param filename: :class:`string`, the name of the remote file
        :param outputfile: :class:`string`, local name of retrived file
          (defaults to filename)

        :rtype: :class:`string`
        :returns: the name of the output file

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`ValueError`:
          no such file (:exc:`KeyError` with disk['file'] syntax)

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

        :param filename: string, the name of the remote file

        :rtype: :class:`bool`
        :returns: whether or not the deletion was successful

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`ValueError`: no such file
          (:exc:`KeyError` with disk['file'] syntax)

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
"""Named tuple containing the informations on a file"""

class QDir(object):
    """Class for handling files in a disk"""
    def __init__(self, disk):
        self._disk = disk
        self._files = {}


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

    def __contains__(self, item):
        """D.__contains__(k) -> True if D has a key k, else False"""
        return item in self.list_files()

    def __iter__(self):
        return iter(self.list_files())

    def add_file(self, filename, dest=None):
        """register a file as to be sent to the disk

        :param filename: :class:`string`, name of the local file
        :param dest: :class:`string`, name of the remote file
          (defaults to filename)
        """
        if dest is None:
            dest = filename
        self._files[dest] = filename

    def get_file(self, filename, outputfile=None):
        """get a file from the disk, you can also use disk['file']
        if given file is not on the disk but registered to be sent,
        return it instead

        :param filename: :class:`string`, the name of the remote file
        :param outputfile: :class:`string`, local name of retrived file
          (defaults to filename)

        :rtype: :class:`string`
        :returns: the name of the output file

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`ValueError`: no such file
          (:exc:`KeyError` with disk['file'] syntax)

        """
        if filename in [f.name for f in self._disk.list_files()]:
            return self._disk[filename]
        return self._files[filename]

    def delete_file(self, filename):
        """delete a file from the disk, and unregister it
        equivalent to del disk['file']

        :param filename: string, the name of the remote file

        :rtype: :class:`bool`
        :returns: whether or not the deletion was successful

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials

          :exc:`ValueError`: no such file
          (:exc:`KeyError` with disk['file'] syntax)

        """
        local = False
        remote = False
        try:
            del self._disk[filename]
            local = True
        except KeyError: pass

        try:
            del self._disk[filename]
            remote = True
        except KeyError: pass

        if not (local or remote):
            raise ValueError('unknown file {}'.format(filename))

    def list_files(self):
        """list files on the disk, and registered files

        :rtype: list of :class:`str`
        :returns: list of the files on the disk

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials
        """
        ret = [f.name for f in self._disk.list_files()]
        ret.extend(self._files.keys())
        return ret

    def push(self):
        """send registered files to the disk

        :raises:
          :exc:`MissingDiskException` : the disk is not on the server

          :exc:`HTTPError`: unhandled http return code

          :exc:`apy.connection.UnauthorizedException`: invalid credentials
        """
        for key, value in self._files.items():
            self._disk[key] = value
            del self._files[key]

##############
# Exceptions #
##############

class MissingDiskException(Exception):
    """Non existant disk"""
    def __init__(self, name):
        super(MissingDiskException, self).__init__(
            "Disk {} does not exist or has been deleted".format(name))
