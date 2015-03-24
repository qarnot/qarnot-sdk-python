"""Module for disk object."""

from __future__ import print_function

from qapy import get_url, raise_on_error
import os.path as path
import posixpath as ppath
import os
import threading

class QDisk(object):
    """Represents a resource/result disk on the cluster.

    This class is the interface to manage resources or results from a
    :class:`qapy.task.QTask`.

    .. note::
       Paths given as 'remote' arguments,
       (or as path arguments for :func:`QDisk.directory`)
       **must** be valid unix-like paths.
    """

    #Creation#
    def __init__(self, jsondisk, connection):
        """Initialize a disk from a dictionary.

        :param dict jsondisk: Dictionary representing the disk,
          must contain following keys:

            * id: string, the disk's UUID

            * description: string, a short description of the disk

        :param :class:`qapy.connection.QApy` connection:
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
        Create a disk on a cluster.

        :param :class:`qapy.connection.QApy` connection:
          represents the cluster on which to create the disk
        :param str description: a short description of the disk
        :param bool force: it will delete an old unlocked disk
          if maximum number of disks is reached for resources and results
        :param bool lock: prevents the disk to be removed
          by a subsequent :meth:`qapy.connection.QApy.create_task` with
          *force* set to True.

        :rtype: :class:`QDisk`
        :returns: The created :class:`QDisk`.

        :raises qapy.QApyException: API general error, see message for details
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
            raise_on_error(response)

        disk_id = response.json()
        return cls._retrieve(connection, disk_id['guid'])


    @classmethod
    def _retrieve(cls, connection, disk_id):
        """Retrieve information of a disk on a cluster.

        :param :class:`qapy.connection.QApy` connection: the cluster
            to get the disk from
        :param str disk_id: the UUID of the disk to retrieve

        :rtype: :class:`QDisk`
        :returns: The retrieved disk.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        response = connection._get(get_url('disk info', name=disk_id))

        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       disk_id)
        raise_on_error(response)

        return cls(response.json(), connection)

    #Disk Management#

    def delete(self):
        """Delete the disk represented by this :class:`QDisk`.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        response = self._connection._delete(
            get_url('disk info', name=self._name))

        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._name)
        raise_on_error(response)

    def get_archive(self, extension='zip', local=None):
        """Get an archive of this disk's content.

        :param str extension: in {'tar', 'tgz', 'zip'},
          format of the archive to get
        :param str local: name of the file to output to

        :rtype: :class:`str`
        :returns:
         The filename of the retrieved archive.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
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
            raise ValueError('invalid file format : {0}', extension)
        else:
            raise_on_error(response)

        local = local or ".".join([self._name, extension])
        if path.isdir(local):
            local = path.join(local, ".".join([self._name, extension]))

        with open(local, 'wb') as f_local:
            for elt in response.iter_content():
                f_local.write(elt)
        return local


    def list_files(self):
        """List files on the whole disk.

        :rtype: List of :class:`QFileInfo`.
        :returns: List of the files on the disk.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """

        self.flush()

        response = self._connection._get(
            get_url('tree disk', name=self._name))
        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._name)
        raise_on_error(response)
        return [QFileInfo(**f) for f in response.json()]

    def directory(self, directory=''):
        """List files in a directory of the disk. Doesn't go through
        subdirectories.

        :param str directory: path of the directory to inspect.
          Must be unix-like.

        :rtype: List of :class:`QFileInfo`.
        :returns: Files in the given directory on the :class:`QDisk`.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials

        .. note::
           Paths in results are relative to the *directory* argument.
        """

        self.flush()

        response = self._connection._get(
            get_url('ls disk', name=self._name, path=directory))
        if response.status_code == 404:
            if response.json()['message'] == 'no such disk':
                raise MissingDiskException(response.json()['message'],
                                           self._name)
        raise_on_error(response)
        return [QFileInfo(**f) for f in response.json()]

    def flush(self):
        """Ensure all files added through :meth:`add_file`/:meth:`add_directory`
        are on the disk.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
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

    def add_link(self, target, linkname):
        """Create link between files on the disk

        :param str target: name of the existing file to duplicate
        :param str linkname: name of the created file

        .. warning::
           File size is counted twice, this method is meant to save upload time, not space.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        data = [
            {
                "target" : target,
                "linkName" : linkname
            }
        ]
        url = get_url('link disk', name=self._name)
        response = self._connection._post(url, json=data)
        raise_on_error(response)

    def add_file(self, local, remote=None, mode=None):
        """Add a file on the disk.

        .. note::
           You can also use **disk[remote] = local**

        .. warning::
           In non blocking mode, you may receive an exception during an other
           operation (like :meth:`flush`).

        :param str local: name of the local file
        :param str remote: name of the remote file
          (defaults to *local*)
        :param mode: mode with which to add the file
          (defaults to :attr:`~QUploadMode.blocking` if not set by :attr:`QDisk.add_mode`)
        :type mode: :class:`QUploadMode`

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        :raises ValueError: file could not be created
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
        elif mode is QUploadMode.lazy:
            self._filecache[remote] = local
        else:
            thread = threading.Thread(None, self._add_file, remote,
                                      (local, remote))
            thread.start()
            self._filethreads[remote] = thread

    def _add_file(self, filename, dest):
        """Add a file on the disk.

        :param str filename: name of the local file
        :param str dest: name of the remote file
          (defaults to filename)

        :rtype: :class:`bool`
        :returns: whether the file has been successfully added

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """

        with open(filename, 'rb') as f_local:
            response = self._connection._post(
                get_url('update file', name=self._name,
                        path=path.dirname(dest)),
                files={'filedata': (path.basename(dest), f_local)})

            if response.status_code == 404:
                raise MissingDiskException(response.json()['message'],
                                           self._name)
            raise_on_error(response)

    def add_directory(self, local, remote="", mode=None):
        """ Add a directory to the disk. Does not follow symlinks.
        File hierarchy is preserved.

        .. note::
           You can also use **disk[remote] = local**

        .. warning::
           In non blocking mode, you may receive an exception during an other
           operation (like :meth:`flush`).

        :param str local: path of the local directory to add
        :param str remote: path of the directory on remote node
          (defaults to *local*)
        :param mode: the mode with which to add the directory
          (defaults to :attr:`~QDisk.add_mode`)
        :type mode: :class:`QUploadMode`

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: one or more file(s) could not be created
        """
        for dirpath, _, files in os.walk(local):
            remote_loc = dirpath.replace(local, remote, 1)
            for filename in files:
                self.add_file(path.join(dirpath, filename),
                              ppath.join(remote_loc, filename), mode)

    def get_file(self, remote, local=None):
        """Get a file from the disk.

        .. note::
           You can also use **disk[file]**

        .. warning::
           Doesn't work with directories. Prefer the use of :meth:`get_archive`.

        :param str remote: the name of the remote file
        :param str local: local name of the retrieved file
          (defaults to *remote*)

        :rtype: :class:`string`
        :returns: The name of the output file.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: no such file
          (:exc:`KeyError` with disk[file] syntax)
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
            if response.json()['message'] == "No such disk":
                raise MissingDiskException(response.json()['message'],
                                           self._name)
        raise_on_error(response)

        with open(local, 'wb') as f_local:
            for elt in response.iter_content(512):
                f_local.write(elt)
        return local

    def delete_file(self, remote):
        """Delete a file from the disk.

        .. note::
           You can also use **del disk[file]**

        :param str remote: the name of the remote file

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
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
            if response.json()['message'] == "No such disk":
               raise MissingDiskException(response.json()['message'],
                                           self._name)
        raise_on_error(response)

    @property
    def name(self):
        """:type: :class:`string`

        The disk's UUID."""
        return self._name

    @property
    def add_mode(self):
        """:type: :class:`QUploadMode`

        Default mode for adding files.
        """
        return self._add_mode

    @add_mode.setter
    def add_mode(self, value):
        """Add mode setter"""
        self._add_mode = value

    @property
    def description(self):
        """:type: :class:`string`

        The disk's description.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        resp = self._connection._get(get_url('disk info', name=self._name))

        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'],
                                       self.name)
        raise_on_error(resp)

        self._description = resp.json()['description']

        return self._description

    @description.setter
    def description(self, value):
        """Description setter"""
        data = {"description" : value}
        resp = self._connection._put(get_url('disk info', name=self._name),
                                     json=data)

        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'],
                                       self.name)
        raise_on_error(resp)

    @property
    def locked(self):
        """:type: :class:`bool`

        The disk's lock state. If True, prevents the disk to be removed
        by a subsequent :meth:`qapy.connection.QApy.create_task` with *force*
        set to True.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        resp = self._connection._get(get_url('disk info', name=self._name))

        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'],
                                       self.name)
        raise_on_error(resp)

        self._locked = resp.json()['locked']
        return self._locked

    @locked.setter
    def locked(self, value):
        """Change disk's lock state."""
        data = {"locked" : value}
        resp = self._connection._put(get_url('disk info', name=self._name),
                                     json=data)
        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'],
                                       self.name)
        raise_on_error(resp)


    #tostring
    def __str__(self):
        return ("[LOCKED]     - " if self.locked else "[NON LOCKED] - ") + self.name + " - " + self.description
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
        if isinstance(item, QFileInfo):
            item = item.name
        return item in [f.name for f in self.list_files()]

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
    """Named tuple containing informations about a file."""
    def __init__(self, creationDate, name, size, fileFlags, md5Sum):
        self.creation = creationDate
        """:type: :class:`string`

        Timestamp at the creation of the file on the :class:`QDisk`."""
        self.name = name
        """:type: :class:`string`

        Path of the file on the :class:`QDisk`."""
        self.size = size
        """:type: :class:`int`

        Size of the file on the :class:`QDisk` (in Bytes)."""
        self.directory = fileFlags == 'directory'
        """:type: :class:`bool`

        Is the file a directory."""

        self.md5sum = md5Sum
        """:type: :class:`string`
        MD5 Sum of the file"""

    def __repr__(self):
        template = 'QFileInfo(creation={0}, name={1}, size={2}, directory={3})'
        return template.format(self.creation, self.name, self.size,
                               self.directory)

class QUploadMode(object):
    """How to add files on a :class:`QDisk`."""
    blocking = 0
    """Call to :func:`~QDisk.add_file` :func:`~QDisk.add_directory`
    or blocks until file is done uploading."""
    background = 1
    """Launch a background thread for uploading."""
    lazy = 2
    """Actual uploading is made by the :func:`~QDisk.flush` method call."""

##############
# Exceptions #
##############

class MissingDiskException(Exception):
    """Non existant disk."""
    def __init__(self, message, name):
        super(MissingDiskException, self).__init__(
            "{0}: {1} ".format(message, name))

class MaxDiskException(Exception):
    """Max number of disks reached."""
    pass
