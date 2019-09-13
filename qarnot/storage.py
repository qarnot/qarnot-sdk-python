"""Storage prototype"""

# Copyright 2017 Qarnot computing
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import os
import os.path


class Storage(object):
    """Common architecture for storage providers
    """

    def get_all_files(self, output_dir, progress=None):
        """Get all files from the storage.

        :param str output_dir: local directory for the retrieved files.
        :param progress: can be a callback (read,total,filename)  or True to display a progress bar
        :type progress: bool or function(float, float, str)
        :raises qarnot.exceptions.MissingBucketException: the bucket is not on the server
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. warning:: Will override *output_dir* content.

        """

        for file_info in self:
            outpath = os.path.normpath(file_info.key.lstrip('/'))
            self.get_file(file_info.key, os.path.join(output_dir, outpath), progress)

    def __init__(self):
        self._uuid = None

    def _not_implemented(self):
        raise NotImplementedError("Class %s doesn't implement %s" % (self.__class__.__name__, inspect.stack()[1][3]))

    def list_files(self):
        """List files on the storage.

        ... note:
            File object returned *must* have a `key` property.

        :returns: List of the files on the storage.
        """
        self._not_implemented()

    def _download_file(self, remote, local, progress=None):
        """Actual file downloader.

        :param remote: the name of the remote file
        :type remote: str
        :param str local: local name of the retrieved file  (defaults to *remote*)
        :param progress: can be a callback (read,total,filename)  or True to display a progress bar
        :type progress: bool or function(float, float, str)
        :rtype: :class:`str`
        :returns: The name of the output file.
        """
        self._not_implemented()

    def get_file(self, remote, local=None, progress=None):
        """Get a file from the storage.
        Create needed subfolders.


        :param remote: the name of the remote file
        :type remote: str
        :param str local: local name of the retrieved file  (defaults to *remote*)
        :param progress: can be a callback (read,total,filename)  or True to display a progress bar
        :type progress: bool or function(float, float, str)
        :rtype: :class:`str`
        :returns: The name of the output file.

        :raises ValueError: no such file
        """

        def make_dirs(_local):
            """Make directory if needed"""
            directory = os.path.dirname(_local)
            if directory != '' and not os.path.exists(directory):
                os.makedirs(directory)

        if local is None:
            local = os.path.basename(remote)

        if os.path.isdir(local):
            local = os.path.join(local, os.path.basename(remote))

        make_dirs(local)

        if os.path.isdir(local):
            return

        return self._download_file(remote, local, progress)

    def copy_file(self, source, dest):
        """Create a copy of a file

        :param str source: name of the existing file to duplicate
        :param str dest: name of the created file
        """
        self._not_implemented()

    def add_directory(self, local, remote):
        """ Add a directory to the storage. Does not follow symlinks.
        File hierarchy is preserved.


        :param str local: path of the local directory to add
        :param str remote: path of the directory on remote node
          (defaults to *local*)

        :raises IOError: not a valid directory
        """
        self._not_implemented()

    def add_file(self, local_or_file, remote):
        """Add a local file or a Python File on the storage.

        .. note::
           You can also use **object[remote] = local**

        :param local_or_file: path of the local file or an opened Python File
        :type local_or_file: str or File
        :param str remote: name of the remote file
          (defaults to *local_or_file*)

        """
        self._not_implemented()

    def delete_file(self, remote):
        """Delete a file from the storage.

        :param str remote: the name of the remote file
        """
        self._not_implemented()

    def update(self, flush=None):
        """Update object from remote endpoint

        :param bool flush: bypass cache
        """
        self._not_implemented()

    def flush(self):
        """Ensure all background uploads are complete
        """
        self._not_implemented()

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
        return item in self.list_files()

    def __iter__(self):
        """x.__iter__() <==> iter(x)"""
        return iter(self.list_files())

    def __eq__(self, other):
        """x.__eq__(y) <==> x == y"""
        if isinstance(other, self.__class__):
            return self._uuid == other._uuid
        return False

    def __ne__(self, other):
        """x.__ne__(y) <==> x != y"""
        return not self.__eq__(other)
