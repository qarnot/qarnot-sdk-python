"""module for disk object"""

from __future__ import print_function

from qapy import get_url
import os.path as path
import posixpath as ppath
import os
import threading
from enum import Enum

class QDisk(object):
    """represents a ressource disk on the cluster

    this class is the interface to manage ressources or results from a
    :class:`qapy.task.Qtask`

    .. note::
       paths given as 'remote' arguments,
       (or as path arguments for :func:`QDisk.ls`)
       **Must** be valid unix-like paths
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
        self._locked = jsondisk["locked"]
        self._connection = connection
        self._filethreads = {}
        self._filecache = {}
        self._add_mode = QUploadMode.blocking

    @classmethod
    def _create(cls, connection, description, force=False, lock=False):
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
            "description" : description,
            "locked" : lock
            }
        url = get_url('disk force') if force else get_url('disk folder')
        response = connection._post(url, json=data)
        if response.status_code == 403:
            raise MaxDiskException(response.json()['message'])
        else:
            response.raise_for_status()

        disk_id = response.json()
        return cls._retrieve(connection, disk_id['guid'])


    @classmethod
    def _retrieve(cls, connection, disk_id):
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

        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._name)

        response.raise_for_status()

    def get_archive(self, extension='zip', local=None):
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
            raise ValueError('invalid file format : {}', extension)
        else:
            response.raise_for_status()

        local = local or ".".join([self._name, extension])
        if path.isdir(local):
            local = path.join(local, ".".join([self._name, extension]))

        with open(local, 'wb') as f_local:
            for elt in response.iter_content():
                f_local.write(elt)
        return local


    def list_files(self):
        """list files on the whole disk

        :rtype: list of :class:`QFileInfo`
        :returns: list of the files on the disk

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """

        self.sync()

        response = self._connection._get(
            get_url('tree disk', name=self._name))
        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._name)
        elif response.status_code != 200:
            response.raise_for_status()
        return [QFileInfo(**f) for f in response.json()]

    def directory(self, directory=''):
        """list files in a directory of the disk

        :param str path: the path of the directory to examine

        :rtype: list of :class:`QFileInfo`
        :returns: files in given directory on the qdisk

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials

        .. note::
           paths in results are given relatively to the
           directory *path* argument refers to
        """

        self.sync()

        response = self._connection._get(
            get_url('ls disk', name=self._name, path=directory))
        if response.status_code == 404:
            if response.json()['message'] == 'no such disk':
                raise MissingDiskException(response.json()['message'],
                                           self._name)
            else:
                raise ValueError('{}: {}'.format(response.json()['message'],
                                                 directory))
        elif response.status_code != 200:
            response.raise_for_status()
        return [QFileInfo(**f) for f in response.json()]

    def sync(self):
        """ensure all files added through :meth:`add_file` are on the disk

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        """
        for thread in self._filethreads.values():
            thread.join()

        self._filethreads.clear()

        for remote, local in self._filecache.items():
            self._add_file(local, remote)

        self._filecache.clear()

    def add_file(self, local, remote=None, mode=None):
        """add a file to the disk (you can also use disk[remote] = local)

        :param str local: name of the local file
        :param str remote: name of the remote file
          (defaults to filename)
        :param mode: the mode with which to add the file
          (defaults to disk.add_mode)
        :type mode: :class:`QUploadMode`

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

        if mode is QUploadMode.blocking:
            return self._add_file(local, remote)
        elif mode is QUploadMode.delayed:
            self._filecache[remote] = local
        else:
            thread = threading.Thread(None, self._add_file, remote,
                                      (local, remote))
            thread.start()
            self._filethreads[remote] = thread

    def _add_file(self, filename, dest):
        """add a file to the disk (you can also use disk[dest] = filename)

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
        :raises ValueError: file could not be created
        """

        with open(filename, 'rb') as f_local:
            response = self._connection._post(
                get_url('update file', name=self._name,
                        path=path.dirname(dest)),
                files={'filedata': (path.basename(dest), f_local)})

            if response.status_code == 404:
                raise MissingDiskException(response.json()['message'],
                                           self._name)
            elif response.status_code == 403:
                raise IOError(response.json()['message'])
            elif response.status_code == 400:
                raise ValueError(response.json()['message'])
            else:
                response.raise_for_status()

    def add_directory(self, local, remote="", mode=None):
        """ add a directory to the disk, do not follow symlinks,
        the internal structure is preserved
        (you can also use disk[dest] = filename)

        :param str local: path of the local directory to add
        :param str remote: path of the directory on remote node
        :param mode: the mode with hich to add the file
          (defaults to disk.add_mode)
        :type mode: :class:`QUploadMode`

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        """
        for dirpath, _, files in os.walk(local):
            remote_loc = dirpath.replace(local, remote, 1)
            for filename in files:
                self.add_file(path.join(dirpath, filename),
                              ppath.join(remote_loc, filename), mode)

    def get_file(self, remote, local=None):
        """get a file from the disk, you can also use disk['file']

        :param str remote: the name of the remote file
        :param str local: local name of retrived file
          (defaults to filename)

        :rtype: :class:`string`
        :returns: the name of the output file

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: no such file
          (:exc:`KeyError` with disk['file'] syntax)
        """
        if isinstance(remote, QFileInfo):
            remote = remote.name

        pending = self._filethreads.get(remote)
        if pending is not None: #ensure file is done uploading
            pending.join()

        if remote in self._filecache:
            self._add_file(remote, self._filecache[remote])
            del self._filecache[remote]

        if local is None:
            local = path.basename(remote)

        if path.isdir(local):
            local = path.join(local, path.basename(remote))

        response = self._connection._get(
            get_url('update file', name=self._name, path=remote),
            stream=True)

        if response.status_code == 404:
            if response.json()['message'] != "No such disk":
                raise ValueError('unknown file {}'.format(remote))
            else:
                raise MissingDiskException(response.json()['message'],
                                           self._name)
        else:
            response.raise_for_status() #raise nothing if 2XX

        with open(local, 'wb') as f_local:
            for elt in response.iter_content(512):
                f_local.write(elt)
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

        if isinstance(remote, QFileInfo):
            remote = remote.name

        response = self._connection._delete(
            get_url('update file', name=self._name, path=remote))

        if response.status_code == 404:
            if response.json()['message'] != "No such disk":
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
        """useless docstring to please pylint"""
        if isinstance(value, QUploadMode):
            self._add_mode = value
        else:
            raise TypeError('add_mode must be a QUploadMode value')

    @property
    def description(self):
        """the disk's description

        :raises MissingDiskException: the disk is not on the server
        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        resp = self._connection._get(get_url('disk info', name=self._name))

        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'],
                                       self.name)
        elif resp.status_code != 200:
            resp.raise_for_status()

        self._description = resp.json()['description']

        return self._description

    @description.setter
    def description(self, value):
        """useless docstring to please pylint"""
        data = {"description" : value}
        resp = self._connection._put(get_url('disk info', name=self._name),
                                     json=data)

        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'],
                                       self.name)
        else:
            resp.raise_for_status()


    #operators#

    def __getitem__(self, filename):
        """x.__getitem__(y) <==> x[y]"""
        try:
            return self.get_file(filename)
        except ValueError:#change error into keyerror if missing file
            raise KeyError(filename)

    def __setitem__(self, dest, filename):
        """x.__setitem__(i, y) <==> x[i]=y"""
        if path.isdir(filename):
            return self.add_directory(filename, dest)
        return self.add_file(filename, dest)

    def __delitem__(self, filename):
        """x.__delitem__(y) <==> del x[y]"""
        try:
            return self.delete_file(filename)
        except ValueError: #change error into keyerror if missing file
            raise KeyError(filename)

    def __contains__(self, item):
        """D.__contains__(k) -> True if D has a key k, else False"""
        return item in self.list_files()

    def __iter__(self):
        """x.__iter__() <==> iter(x)"""
        return iter(self.list_files())

###################
# Utility Classes #
###################

#uncomment me if named tuple are choosen
#QFileInfo = collections.namedtuple('QFileInfo',
#                                  ['creation_date', 'name', 'size', 'type'])
#"""Named tuple containing the informations on a file"""

class QFileInfo(object):
    """Named tuple containing the information on a file"""
    def __init__(self, creationDate, name, size, fileFlags):
        self.creation = creationDate
        """timestamp at which file was created on the :class:`QDisk`"""
        self.name = name
        """path to the file on the qdisk"""
        self.size = size
        """size of the file on the qdisk (in Bytes)"""
        self.directory = fileFlags == 'directory'
        """is the file a directory"""

    def __repr__(self):
        template = 'QFileInfo(creation={0}, name={1}, size={2}, directory={3})'
        return template.format(self.creation, self.name, self.size,
                               self.directory)

class QUploadMode(Enum):
    """How to add files on a :class:`QDisk`"""
    blocking = 0 #: call to add_file blocks until file is done uploading
    background = 1 #: launch a background thread
    delayed = 2
    lazy= 2
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
