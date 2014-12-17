"""module for disk object"""

from __future__ import print_function

from qapy import get_url
import os.path as path
import posixpath as ppath
import os
import json
import collections
import threading
from enum import Enum

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

        :param qapy.connection.QApy connection:
          the cluster on which the disk is
        """
        self._name = jsondisk["id"]
        self._description = jsondisk["description"]
        self._ro = jsondisk["readOnly"]
        self._connection = connection
        self._filethreads = {}
        self._filecache = {}
        self._add_mode = QAddMode.blocking

    @classmethod
    def _create(cls, connection, description):
        """
        create a disk on a cluster

        :param qapy.connection.QApy connection:
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
        if response.status_code == 403:
            raise MaxDiskException(response.json()['message'])
        else:
            response.raise_for_status()

        disk_id = response.json()
        return cls.retrieve(connection, disk_id['guid'])


    @classmethod
    def retrieve(cls, connection, disk_id):
        """retrieve information of a disk on a cluster

        :param qapy.connection.QApy connection: the cluster
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
            raise MissingDiskException(response.json()['message'],
                                       disk_id)
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
            raise MissingDiskException(response.json()['message'],
                                       self._name)

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
            raise MissingDiskException(response.json()['message'],
                                       self._name)
        elif response.status_code == 400:
            raise ValueError('invalid file format : {}'.extension)
        else:
            response.raise_for_status()

        output = output or ".".join([self._name, extension])
        if path.isdir(output):
            output = path.join(output, ".".join([self._name, extension]))

        with open(output, 'wb') as f:
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
            get_url('tree disk', name=self._name))
        if (response.status_code == 404):
            raise MissingDiskException(response.json()['message'],
                                       self._name)
        elif response.status_code != 200:
            response.raise_for_status()
        return [QFileInfo(f['creationDate'], f['fileName'], f['size'])
                for f in response.json()]

    def sync(self):
        """ensure all fille added through add file are on the disk

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        """
        for k, t in self._filethreads.items():
            t.join()

        self._filethreads.clear()

        for remote, local in self._filecache.items():
            self._add_file(local, remote)

        self._filecache.clear()

    def add_file(self, local, remote=None, mode=None):
        """add a file to the disk (you can also use disk[remote] = local)

        :param str filename: name of the local file
        :param str dest: name of the remote file
          (defaults to filename)
        :param mode: the mode with hich to add the file
          (defaults to disk.add_mode)
        :type mode: :class:`QAddMode`

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        """
        mode = mode or self._add_mode
        remote = remote or path.basename(local)

        if isinstance(remote, QFileInfo):
            remote = remote.name

        previous = self._filethreads.get(remote)
        if previous is not None: #ensure no 2 threads write on the same file
            previous.join()
            del self._filethreads[remote]

        if remote in self._filecache: #do not delay a file added differently
            del self._filecache[remote]

        if mode is QAddMode.blocking:
            return self._add_file(local, remote)
        elif mode is QAddMode.delayed:
            self._filecache[remote] = local
        else:
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

        if self._ro:
            raise TypeError("tried to write on Read only disk")

        with open(filename, 'rb') as f:
            response = self._connection._post(
                get_url('update file', name=self._name,
                        path=path.dirname(dest)),
                files={'filedata': (path.basename(dest),f)})

            if (response.status_code == 404):
                raise MissingDiskException(response.json()['message'],
                                           self._name)
            elif response.status_code == 403:
                raise IOError("disk full")
            else:
                response.raise_for_status()

    def add_dir(self, local, remote="", mode=None):
        """ add a directory to the disk, do not follow symlinks
        the internal structure is preserved

        :param str local: path of the local directory to add
        :param str remote: path of the directory on remote node
        :param QAddMode mode: the mode with hich to add the file
          (defaults to disk.add_mode)

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
                              ppath.join(remote_loc, filename), mode)

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

        if remote in self._filecache:
            self._add_file(remote, self._filecache[remote])
            del self._filecache[remote]

        #remote = remote.lstrip('/')

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
                raise MissingDiskException(response.json()['message'],
                                           self._name)
        else:
            response.raise_for_status() #raise nothing if 2XX

        with open(local, 'wb') as f:
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

        if remote in self._filecache:
            self._add_file(remote, self._filecache[remote])
            del self._filecache[remote]

        if isinstance(remote , QFileInfo):
            remote = remote.name

        response = self._connection._delete(
            get_url('update file', name=self._name, path=remote))

        if response.status_code == 404:
            if response.json()['errorMessage'] != "No such disk":
                raise ValueError('unknown file {}'.format(remote))
            else:
                raise MissingDiskException(response.json()['message'],
                                           self._name)
        else:
            response.raise_for_status() #raise nothing if 2XX

    @property
    def name(self):
        """the disk's UUID"""
        return self._name

    @property
    def add_mode(self):
        """default mode for adding files"""
        return self._add_mode

    @add_mode.setter
    def add_mode(self, value):
        if isinstance(value, QAddMode):
            self._add_mode = value
        else:
            raise TypeError('add_mode must be a QAddMode value')

    @property
    def readonly(self):
        """whether or not the disk is read only
        not that trying to add a file on a readonly disk will raise
        a :exc:`TypeError`
        """
        return self._ro

    @property
    def description(self):
        return self._description
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

class QAddMode(Enum):
    """How to add files in a :class:`QDisk`"""
    blocking = 0 #: call to add_file blocks until file is done uploading
    background = 1 #: launch a background thread
    delayed = 2
    """actual uploading is made by the :func:`QDisk.sync` method call"""

##############
# Exceptions #
##############

class MissingDiskException(Exception):
    """Non existant disk"""
    def __init__(self, message, name):
        super(MissingDiskException, self).__init__(
            "{}: {} ".format(message, name))

class MaxDiskException(Exception):
    """max number of disks reached"""
    pass
