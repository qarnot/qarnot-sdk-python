"""Module for disk object."""

from __future__ import print_function

from qapy import get_url, raise_on_error
import posixpath
import os
import os.path
import hashlib
import datetime
import threading
import itertools


class QDisk(object):
    """Represents a resource/result disk on the cluster.

    This class is the interface to manage resources or results from a
    :class:`qapy.task.QTask`.

    .. note::
       Paths given as 'remote' arguments,
       (or as path arguments for :func:`QDisk.directory`)
       **must** be valid unix-like paths.
    """

    # Creation
    def __init__(self, jsondisk, connection):
        """Initialize a disk from a dictionary.

        :param dict jsondisk: Dictionary representing the disk,
          must contain following keys:

            * id: string, the disk's UUID

            * description: string, a short description of the disk

        :param :class:`qapy.connection.QApy` connection:
          the cluster on which the disk is
        """
        self._id = jsondisk["id"]
        self._description = jsondisk["description"]
        self._file_count = jsondisk["fileCount"]
        self._used_space_bytes = jsondisk["usedSpaceBytes"]
        self._locked = jsondisk["locked"]
        if "global" in jsondisk:
            self._global = jsondisk["global"]
        else:
            self._global = {}
        self._connection = connection
        self._filethreads = {}  # A dictionary containing key:value where key is
        #  the remote destination on disk, and value a running thread.
        self._filecache = {}  # A dictionary containing key:value where key is
        #  the remote destination on disk, and value an opened Python File.
        self._add_mode = QUploadMode.blocking

    @classmethod
    def _create(cls, connection, description, force=False, lock=False,
                global_disk=False):
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
            "description": description,
            "locked": lock,
            "global": global_disk
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

    # Disk Management
    def update(self):
        """Update disk instance from remote API

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        response = self._connection._get(get_url('disk info', name=self._id))
        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._id)
        raise_on_error(response)

        jsondisk = response.json()
        self._id = jsondisk["id"]
        self._description = jsondisk["description"]
        self._file_count = jsondisk["fileCount"]
        self._used_space_bytes = jsondisk["usedSpaceBytes"]
        self._locked = jsondisk["locked"]
        self._file_count = jsondisk["fileCount"]
        self._used_space_bytes = jsondisk["usedSpaceBytes"]

    def delete(self):
        """Delete the disk represented by this :class:`QDisk`.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        response = self._connection._delete(
            get_url('disk info', name=self._id))

        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._id)
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
            get_url('get disk', name=self._id, ext=extension),
            stream=True)

        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._id)
        elif response.status_code == 400:
            raise ValueError('invalid file format : {0}', extension)
        else:
            raise_on_error(response)

        local = local or ".".join([self._id, extension])
        if os.path.isdir(local):
            local = os.path.join(local, ".".join([self._id, extension]))

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
            get_url('tree disk', name=self._id))
        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'],
                                       self._id)
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
            get_url('ls disk', name=self._id, path=directory))
        if response.status_code == 404:
            if response.json()['message'] == 'no such disk':
                raise MissingDiskException(response.json()['message'],
                                           self._id)
        raise_on_error(response)
        return [QFileInfo(**f) for f in response.json()]

    def sync_directory(self, directory, verbose=False):
        """Synchronize a local directory with the remote disks.

        :param str directory: The local directory to use for synchronization
        :param bool verbose: Print information about synchronization operations

        .. warning::
           Local changes are reflected on the server, a file present on the
           disk but not in the local directory will be deleted from the disk.

           A file present in the directory but not in the disk will be uploaded.

        .. note::
           The following parameters are used to determine whether
           synchronization is required :

              * name
              * size
              * sha1sum
        """
        if not directory.endswith('/'):
            directory = directory + '/'

        filesdict = {}
        for root, _, files in os.walk(directory):
            for file_ in files:
                filepath = os.path.join(root, file_)
                name = filepath[len(directory) - 1:]
                filesdict[name] = filepath
        self.sync_files(filesdict, verbose)

    def sync_files(self, files, verbose=False):
        """Synchronize files  with the remote disks.

        :param dict files: Dictionary of synchronized files
        :param bool verbose: Print information about synchronization operations

        Dictionary key is the remote file path while value is the local file
        path.

        .. warning::
           Local changes are reflected on the server, a file present on the
           disk but
           not in the local directory will be deleted from the disk.

           A file present in the directory but not in the disk will be uploaded.

        .. note::
           The following parameters are used to determine whether
           synchronization is required :

              * name
              * size
              * sha1sum
        """
        def generate_file_sha1(filepath, blocksize=2**20):
            """Generate SHA1 from file"""
            sha1 = hashlib.sha1()
            with open(filepath, "rb") as file_:
                while True:
                    buf = file_.read(blocksize)
                    if not buf:
                        break
                    sha1.update(buf)
            return sha1.hexdigest()

        def create_qfi(name, filepath):
            """Create a QFI from a file"""
            if not name.startswith('/'):
                name = '/' + name
            mtime = os.path.getmtime(filepath)
            dtutc = datetime.datetime.utcfromtimestamp(mtime)
            dtutc = dtutc.replace(microsecond=0)
            size = os.stat(filepath).st_size
            qfi = QFileInfo(dtutc, name, size, "file", generate_file_sha1(filepath))
            qfi.filepath = filepath
            return qfi

        localfiles = []
        for name, filepath in files.items():
            qfi = create_qfi(name, filepath)
            localfiles.append(qfi)

        local = set(localfiles)
        remote = set(self.list_files())

        adds = local - remote
        removes = remote - local

        sadds = sorted(adds, key=lambda x: x.sha1sum)
        groupedadds = [list(g) for _, g in itertools.groupby(
            sadds, lambda x: x.sha1sum)]

        for file_ in removes:
            renames = [x for x in adds if x.sha1sum == file_.sha1sum]
            if len(renames) > 0:
                for dup in renames:
                    if verbose:
                        print("Copy", file_.name, "to", dup.name)
                    self.add_link(file_.name, dup.name)
            if verbose:
                print ("remove ", file_.name)
                self.delete_file(file_.name)

        remote = self.list_files()

        for entry in groupedadds:
            try:
                rem = next(x for x in remote if x.sha1sum == entry[0].sha1sum)
                if rem.name == entry[0].name:
                    continue
                if verbose:
                    print("Link:", rem.name, "<-", entry[0].name)
                self.add_link(rem.name, entry[0].name)
            except StopIteration:
                if verbose:
                    print("Upload:", entry[0].name)
                self.add_file(entry[0].filepath, entry[0].name)
            if len(entry) > 1:  # duplicate files
                for link in entry[1:]:
                    if verbose:
                        print("Link:", entry[0].name, "<-", link.name)
                    self.add_link(entry[0].name, link.name)

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

        for remote, file_ in self._filecache.items():
            self._add_file(file_, remote)

        self._filecache.clear()

    def add_link(self, target, linkname):
        """Create link between files on the disk

        :param str target: name of the existing file to duplicate
        :param str linkname: name of the created file

        .. warning::
           File size is counted twice, this method is meant to save upload
           time, not space.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        data = [
            {
                "target": target,
                "linkName": linkname
            }
        ]
        url = get_url('link disk', name=self._id)
        response = self._connection._post(url, json=data)
        raise_on_error(response)

    def _is_executable(self, file):
        try:
            return os.access(file.name, os.X_OK)
        except IOError:
            return False

    def add_file(self, local_or_file, remote=None, mode=None, **kwargs):
        """Add a local file or a Python File on the disk.

        .. note::
           You can also use **disk[remote] = local**

        .. warning::
           In non blocking mode, you may receive an exception during an other
           operation (like :meth:`flush`).

        :param str|File local_or_file: path of the local file or an opened
          Python File
        :param str remote: name of the remote file
          (defaults to *local_or_file*)
        :param mode: mode with which to add the file
          (defaults to :attr:`~QUploadMode.blocking` if not set by
          :attr:`QDisk.add_mode`)
        :type mode: :class:`QUploadMode`

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises TypeError: trying to write on a R/O disk
        :raises IOError: user space quota reached
        :raises ValueError: file could not be created
        """
        mode = mode or self._add_mode

        if isinstance(local_or_file, str):
            file_ = open(local_or_file, 'rb')
        else:
            file_ = local_or_file

        dest = remote or os.path.basename(file_.name)
        if isinstance(dest, QFileInfo):
            dest = dest.name

        # Ensure 2 threads do not write on the same file
        previous = self._filethreads.get(dest)
        if previous is not None:
            previous.join()
            del self._filethreads[dest]

        # Do not delay a file added differently
        if dest in self._filecache:
            self._filecache[dest].close()
            del self._filecache[dest]

        if mode is QUploadMode.blocking:
            return self._add_file(file_, dest, **kwargs)
        elif mode is QUploadMode.lazy:
            self._filecache[dest] = file_
        else:
            thread = threading.Thread(None, self._add_file, dest, (file_, dest), **kwargs)
            thread.start()
            self._filethreads[dest] = thread

    def _add_file(self, file_, dest, **kwargs):
        """Add a file on the disk.

        :param File file_: an opened Python File
        :param str dest: name of the remote file (defaults to filename)

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """

        try:
            file_.seek(0)
        except AttributeError:
            pass

        url = get_url('update file', name=self._id, path=os.path.dirname(dest))

        try:
            # If requests_toolbelt is installed, we can use its
            # MultipartEncoder to stream the upload and save memory overuse
            from requests_toolbelt import MultipartEncoder  # noqa
            m = MultipartEncoder(
                fields={'filedata': (os.path.basename(dest), file_)})
            response = self._connection._post(
                url,
                data=m,
                headers={'Content-Type': m.content_type})
        except ImportError:
            response = self._connection._post(
                url,
                files={'filedata': (os.path.basename(dest), file_)})

        if response.status_code == 404:
            raise MissingDiskException(response.json()['message'], self._id)
        raise_on_error(response)

        # Update file settings
        if 'executable' not in kwargs:
            kwargs['executable'] = self._is_executable(file_)
        self.update_file_settings(dest, **kwargs)

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
        :raises IOError: not a valid directory
        """

        if not os.path.isdir(local):
            raise IOError("Not a valid directory")
        if not remote.endswith('/'):
            remote += '/'
        for dirpath, _, files in os.walk(local):
            remote_loc = dirpath.replace(local, remote, 1)
            for filename in files:
                self.add_file(os.path.join(dirpath, filename),
                              posixpath.join(remote_loc, filename), mode)

    def get_file_iterator(self, remote, chunk_size=1024):
        """Get a file iterator from the disk.

        .. note::
           This function is a generator, and thus can be used in a for loop

        :param str|QFileInfo remote: the name of the remote file or a QFileInfo
        :param int chunk_size: Size of chunks to be yield

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: no such file
        """

        if isinstance(remote, QFileInfo):
            remote = remote.name

        # Ensure file is done uploading
        pending = self._filethreads.get(remote)
        if pending is not None:
            pending.join()

        if remote in self._filecache:
            try:
                self._filecache[remote].seek(0)
            except AttributeError:
                pass
            while True:
                chunk = self._filecache[remote].read(chunk_size)
                if not chunk:
                    break
                yield chunk
        else:
            response = self._connection._get(
                get_url('update file', name=self._id, path=remote),
                stream=True)

            if response.status_code == 404:
                if response.json()['message'] == "No such disk":
                    raise MissingDiskException(response.json()['message'],
                                               self._id)
            raise_on_error(response)

            for chunk in response.iter_content(chunk_size):
                yield chunk

    def get_all_files(self, output_dir):
        """Get all files the disk.

        :param str output_dir: local directory for the retrieved files.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials

        .. warning:: Will override *output_dir* content.

        """

        for file_info in self:
            outpath = os.path.normpath(file_info.name.lstrip('/'))
            self.get_file(file_info, os.path.join(output_dir,
                                                  outpath))

    def get_file(self, remote, local=None):
        """Get a file from the disk.

        .. note::
           You can also use **disk[file]**

        :param str|QFileInfo remote: the name of the remote file or a QFileInfo
        :param str local: local name of the retrieved file
          (defaults to *remote*)

        :rtype: :class:`str`
        :returns: The name of the output file.

        :raises qapy.disk.MissingDiskException: the disk is not on the server
        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises ValueError: no such file
          (:exc:`KeyError` with disk[file] syntax)
        """

        def make_dirs(_local):
            """Make directory if needed"""
            directory = os.path.dirname(_local)
            if directory != '' and not os.path.exists(directory):
                os.makedirs(directory)

        if isinstance(remote, QFileInfo):
            remote = remote.name

        if local is None:
            local = os.path.basename(remote)

        if os.path.isdir(local):
            local = os.path.join(local, os.path.basename(remote))

        make_dirs(local)
        with open(local, 'wb') as f_local:
            for chunk in self.get_file_iterator(remote):
                f_local.write(chunk)

        return local

    def update_file_settings(self, remote_path, **kwargs):
        settings = dict(**kwargs)

        if len(settings) < 1:
            return

        response = self._connection._put(
            get_url('update file', name=self._id, path=remote_path),
            json=settings)

        if response.status_code == 404:
                if response.json()['message'] == "No such disk":
                    raise MissingDiskException(response.json()['message'],
                                               self._id)
        raise_on_error(response)

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
        dest = remote.name if isinstance(remote, QFileInfo) else remote

        # Ensure 2 threads do not write on the same file
        pending = self._filethreads.get(dest)
        if pending is not None:
            pending.join()

        # Remove the file from local cache if present
        if dest in self._filecache:
            self._filecache[dest].close()
            del self._filecache[dest]
            # The file is not present on the disk so just return
            return

        response = self._connection._delete(
            get_url('update file', name=self._id, path=dest))

        if response.status_code == 404:
            if response.json()['message'] == "No such disk":
                raise MissingDiskException(response.json()['message'],
                                           self._id)
        raise_on_error(response)

    def commit(self):
        """Replicate local changes on the current object instance to the REST API

        :raises qapy.QApyException: API general error, see message for details
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        data = {
            "description": self._description,
            "locked": self._locked,
            "global": self.globally_available,
        }
        resp = self._connection._put(get_url('disk info', name=self._id),
                                     json=data)
        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'],
                                       self._id)
        raise_on_error(resp)

    @property
    def uuid(self):
        """:type: :class:`str`

        The disk's UUID."""
        return self._id

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
        """:type: :class:`str`

        The disk's description.
        """
        return self._description

    @description.setter
    def description(self, value):
        """Description setter"""
        self._description = value

    @property
    def globally_available(self):
        """:type: :class:`bool`

        The disk's global availability. If True, the disk is available for any
        user on the cluster, else it is only available for the owner.
        """
        return self._global

    @globally_available.setter
    def globally_available(self, value):
        """Change disk's global availability."""
        self._global = value

    @property
    def file_count(self):
        """:type: :class:`int`

        The number of files on the disk.
        """
        return self._file_count

    @property
    def used_space_bytes(self):
        """:type: :class:`int`

        The total space used on the disk in bytes.
        """
        return self._used_space_bytes

    @property
    def locked(self):
        """:type: :class:`bool`

        The disk's lock state. If True, prevents the disk to be removed
        by a subsequent :meth:`qapy.connection.QApy.create_task` with *force*
        set to True.
        """
        return self._locked

    @locked.setter
    def locked(self, value):
        """Change disk's lock state."""
        self._locked = value

    def __str__(self):
        return (
            ("[LOCKED]     - " if self.locked else "[NON LOCKED] - ") +
            self.uuid + " - " + self.description
        )

    # Operators
    def __getitem__(self, filename):
        """x.__getitem__(y) <==> x[y]"""
        try:
            return self.get_file(filename)
        except ValueError:
            raise KeyError(filename)

    def __setitem__(self, remote, filename):
        """x.__setitem__(i, y) <==> x[i]=y"""
        if os.path.isdir(filename):
            return self.add_directory(filename, remote)
        return self.add_file(filename, remote)

    def __delitem__(self, filename):
        """x.__delitem__(y) <==> del x[y]"""
        try:
            return self.delete_file(filename)
        except ValueError:
            raise KeyError(filename)

    def __contains__(self, item):
        """D.__contains__(k) -> True if D has a key k, else False"""
        if isinstance(item, QFileInfo):
            item = item.name
        return item in [f.name for f in self.list_files()]

    def __iter__(self):
        """x.__iter__() <==> iter(x)"""
        return iter(self.list_files())

    def __eq__(self, other):
        """x.__eq__(y) <==> x == y"""
        if isinstance(other, self.__class__):
            return self._id == other._id
        return False

    def __ne__(self, other):
        """x.__ne__(y) <==> x != y"""
        return not self.__eq__(other)


# Utility Classes
class QFileInfo(object):
    """Information about a file."""
    def __init__(self, lastChange, name, size, fileFlags, sha1Sum):

        self.lastchange = None
        """:type: :class:`datetime`

        UTC Last change time of the file on the :class:`QDisk`."""

        if isinstance(lastChange, datetime.datetime):
            self.lastchange = lastChange
        else:
            self.lastchange = datetime.datetime.strptime(lastChange,
                                                         "%Y-%m-%dT%H:%M:%SZ")

        self.name = name
        """:type: :class:`str`

        Path of the file on the :class:`QDisk`."""
        self.size = size
        """:type: :class:`int`

        Size of the file on the :class:`QDisk` (in Bytes)."""
        self.directory = fileFlags == 'directory'
        """:type: :class:`bool`

        Is the file a directory."""

        self.sha1sum = sha1Sum
        """:type: :class:`str`
        SHA1 Sum of the file"""

        if not self.directory:
            self.executable = fileFlags == 'executableFile'
            """:type: :class:`bool`
            Is the file executable."""

        self.filepath = None  # Only for sync

    def __repr__(self):
        template = 'QFileInfo(lastchange={0}, name={1}, size={2}, '\
                   'directory={3}, sha1sum={4})'
        return template.format(self.lastchange, self.name, self.size,
                               self.directory, self.sha1sum)

    def __eq__(self, other):
        return (self.name == other.name and
                self.size == other.size and
                self.directory == other.directory and
                self.sha1sum == other.sha1sum)

    def __hash__(self):
        return (hash(self.name) ^
                hash(self.size) ^
                hash(self.directory) ^
                hash(self.sha1sum))


class QUploadMode(object):
    """How to add files on a :class:`QDisk`."""
    blocking = 0
    """Call to :func:`~QDisk.add_file` :func:`~QDisk.add_directory`
    or blocks until file is done uploading."""
    background = 1
    """Launch a background thread for uploading."""
    lazy = 2
    """Actual uploading is made by the :func:`~QDisk.flush` method call."""


# Exceptions
class MissingDiskException(Exception):
    """Non existing disk."""
    def __init__(self, message, name):
        super(MissingDiskException, self).__init__(
            "{0}: {1} ".format(message, name))


class MaxDiskException(Exception):
    """Max number of disks reached."""
    pass
