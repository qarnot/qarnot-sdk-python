"""module for disk object"""

from qapy import get_url
import os.path as path
import posixpath as ppath
import os
import json
import collections
import threading

class QDisk(object):
    """represents a ressource disk on the cluster

    this class is the interface to manage ressources or results from a
    :class:`qapy.task.Qtask`

    .. note::
       paths given as 'remote' arguments **Must** be valid unix-like paths
    """
    #Creation#
    def __init__(self, jsondisk, connection):
        """
        initialize a disk from a dictionnary.

        :param dict jsondisk: dictionnary representing the disk,
          must contain following keys :

            * id: string, the disk's UUID

            * description : string, a short description of the disk

            * readOnly : boolean, is the disk read only

        :param qapy.connection.QConnection connection:
          the cluster on which the disk is
        """
        self._name = jsondisk["id"]
        self.description = jsondisk["description"]
        self.readonly = jsondisk["readOnly"] #make these 3 R/O properties ?
        self._connection = connection
        self._filethreads = {}

    @classmethod
    def _create(cls, connection, description):
        """
        create a disk on a cluster

        :param qapy.connection.QConnection connection:
          represents the cluster on which to create the disk
        :param str description: a short description of the disk

        :rtype: :class:`QDisk`
        :returns: the created disk

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        data = {
            "description" : description
            }
        response = connection._post(get_url('disk folder'), json=data)

        if response.status_code != 200: #raise unexpected status code
            response.raise_for_status()

        disk_id = response.json()
        return cls.retrieve(connection, disk_id['guid'])


    @classmethod
    def retrieve(cls, connection, disk_id):
        """retrieve information of a disk on a cluster

        :param qapy.connection.QConnection connection: the cluster
            to get the disk from
        :param str disk_id: the UUID of the disk to retrieve

        :rtype: :class:`QDisk`
        :returns: the retrieved disk

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        response = connection._get(get_url('disk info', name=disk_id))

        if response.status_code == 404:
            raise MissingDiskException(disk_id)
        elif response.status_code != 200:
            response.raise_for_status()

        return cls(response.json(), connection)

    #Disk Manangment#

    def delete(self):
        """delete the disk represented by this Qdisk

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        response = self._connection._delete(
            get_url('disk info', name=self._name))

        if (response.status_code == 404):
            raise MissingDiskException(self._name)

        response.raise_for_status()

    def get_archive(self, extension='zip', output=None):
        """retrieve an archive of this disk's content

        :param str extension: in {'tar', 'tgz', 'zip'},
          format of the archive to get
        :param str output: name of the file to output to

        :rtype: :class:`str`
        :returns:
         the filename of the retrieved archive

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: invalid extension format
        """
        response = self._connection._get(
            get_url('get disk', name=self._name, ext=extension),
            stream=True)

        if response.status_code == 404:
            raise MissingDiskException(self._name)
        elif response.status_code == 400:
            raise ValueError('invalid file format : {}'.extension)
        else:
            response.raise_for_status()

        output = output or ".".join([self._name, extension])
        if path.isdir(output):
            output = path.join(output, ".".join([self._name, extension]))

        with open(output, 'w') as f:
            for elt in response.iter_content():
                f.write(elt)
        return output


    def list_files(self):
        """list files on the disk as QFileInfo named Tuples

        :rtype: list of :class:`QFileInfo`
        :returns: list of the files on the disk

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        response = self._connection._get(
            get_url('ls disk', name=self._name))
        if (response.status_code == 404):
            raise MissingDiskException(self._name)
        elif response.status_code != 200:
            response.raise_for_status()
        return [QFileInfo._make(f.values()) for f in response.json()]

    def sync(self):
        for k, t in self._filethreads.items():
            t.join()
            del self._filethreads[k]

    def add_file(self, local, remote=None): #self.thread
        """add a file to the disk (yo can also use disk[dest] = filename)

        :param str filename: name of the local file
        :param str dest: name of the remote file
          (defaults to filename)

        :rtype: :class:`bool`
        :returns: whether the file has been successfully added

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        """
        remote = remote or path.basename(local)

        if isinstance(remote, QFileInfo):
            remote = remote.name

        previous = self._filethreads.get(remote)
        if previous is not None: #ensure 2 threads write on the same file
            previous.join()

        t = threading.Thread(None, self._add_file, remote, (local, remote))
        t.start()
        self._filethreads[remote] = t

    def _add_file(self, filename, dest):
        """add a file to the disk (yo can also use disk[dest] = filename)

        :param str filename: name of the local file
        :param str dest: name of the remote file
          (defaults to filename)

        :rtype: :class:`bool`
        :returns: whether the file has been successfully added

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        """

        if self.readonly:
            raise TypeError("tried to write on Read only disk")

        with open(filename) as f:
            response = self._connection._post(
                get_url('update file', name=self._name,
                        path=path.dirname(dest)),
                files={'filedata': (path.basename(dest),f)})

            if (response.status_code == 404):
                raise MissingDiskException(self._name)
            elif response.status_code == 403:
                raise IOError("disk full")
            else:
                response.raise_for_status()
            return response.status_code == 200

    def add_dir(self, local, remote=""):
        """ add a directory to the disk, do not follow symlinks
        the internal structure is preserved

        :param str local: path of the local directory to add
        :param str remote: path of the directory on remote node

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        """
        for dirpath, dirs, files in os.walk(local):
            remote_loc = dirpath.replace(local, remote, 1)
            for filename in files:
                self.add_file(path.join(dirpath, filename),
                              ppath.join(remote_loc, filename))

    def get_file(self, remote, local=None):
        """get a file from the disk, you can also use disk['file']

        :param str filename: the name of the remote file
        :param str outputfile: local name of retrived file
          (defaults to filename)

        :rtype: :class:`string`
        :returns: the name of the output file

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: no such file
          (:exc:`KeyError` with disk['file'] syntax)
        """
        if isinstance(remote , QFileInfo):
            remote = remote.name

        pending = self._filethreads.get(remote)
        if pending is not None: #ensure filr is done uploading
            pending.join()

        remote = remote.lstrip('/')

        if local is None:
            local = path.basename(remote)

        if path.isdir(local):
            local = path.join(local, path.basename(remote))

        response = self._connection._get(
            get_url('update file', name=self._name, path=remote),
            stream=True)

        if response.status_code == 404:
            if response.json()['errorMessage'] != "No such disk":
                raise ValueError('unknown file {}'.format(remote))
            else:
                raise MissingDiskException(self._name)
        else:
            response.raise_for_status() #raise nothing if 2XX

        with open(local, 'w') as f:
            for elt in response.iter_content(512):
                f.write(elt)
        return local

    def delete_file(self, remote):
        """delete a file from the disk, equivalent to del disk['file']

        :param str remote: the name of the remote file

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: no such file
          (:exc:`KeyError` with disk['file'] syntax)

        """
        pending = self._filethreads.get(remote)
        if pending is not None: #ensure 2 threads don't use the same file
            pending.join()

        if isinstance(remote , QFileInfo):
            remote = remote.name

        response = self._connection._delete(
            get_url('update file', name=self._name, path=remote))

        if response.status_code == 404:
            if response.json()['errorMessage'] != "No such disk":
                raise ValueError('unknown file {}'.format(remote))
            else:
                raise MissingDiskException(self._name)
        else:
            response.raise_for_status() #raise nothing if 2XX

    @property
    def name(self):
        """the disk's UUID"""
        return self._name

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

    def __contains__(self, item):
        """D.__contains__(k) -> True if D has a key k, else False"""
        return item in self.list_files()

    def __iter__(self):
        return iter(self.list_files())


###################
# Utility Classes #
###################

QFileInfo = collections.namedtuple('QFileInfo',
                                  ['creation_date', 'name', 'size'])
"""Named tuple containing the informations on a file"""

##############
# Exceptions #
##############

class MissingDiskException(Exception):
    """Non existant disk"""
    def __init__(self, name):
        super(MissingDiskException, self).__init__(
            "Disk {} does not exist or has been deleted".format(name))
