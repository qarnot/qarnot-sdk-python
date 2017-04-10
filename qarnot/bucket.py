"""Module for bucket object."""

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
import hashlib
import sys
import os
import posixpath
from qarnot import storage
import itertools
from boto3.s3.transfer import TransferConfig

# Max size in bytes before uploading in parts.

AWS_UPLOAD_MAX_SIZE = 8 * 1024 * 1024
# Size of parts when uploading in parts
AWS_UPLOAD_PART_SIZE = 8 * 1024 * 1024

s3_multipart_config = TransferConfig(
    multipart_threshold=AWS_UPLOAD_MAX_SIZE,
    multipart_chunksize=AWS_UPLOAD_PART_SIZE,
    max_concurrency=10,
    num_download_attempts=10,
)


class Bucket(storage.Storage):
    """Represents a resource/result bucket.

    This class is the interface to manage resources or results from a
    :class:`qarnot.bucket.Bucket`.

    .. note::
       A :class:`Bucket` must be created with
       :meth:`qarnot.connection.Connection.create_bucket`
       or retrieved with :meth:`qarnot.connection.Connection.buckets`, :meth:`qarnot.connection.Connection.retrieve_bucket`,
       or :meth:`qarnot.connection.Connection.retrieve_or_create_bucket`.

    .. note::
       Paths given as 'remote' arguments,
       (or as path arguments for :func:`Bucket.directory`)
       **must** be valid unix-like paths.
    """

    def __init__(self, connection, name):
        self._connection = connection
        self._uuid = name

        self._connection.s3client.create_bucket(Bucket=name)

    def delete(self, empty=False):
        """Get an archive of this disk's content.

        :param bool empty: Remove all objects from bucket. Only empty buckets can be removed.

        """
        if empty:
            bucket = self._connection.s3resource.Bucket(self._uuid)
            objectlist = list(bucket.objects.all())
            n = 1000  # delete object count max request

            if sys.version_info >= (3, 0):
                listofobjectlist = [[{'Key': x.key} for x in objectlist[i:i + n]] for i in range(0, len(objectlist), n)]
            else:
                # noinspection PyUnresolvedReferences
                listofobjectlist = [[{'Key': x.key} for x in objectlist[i:i + n]] for i in xrange(0, len(objectlist), n)]  # noqa
            for item in listofobjectlist:
                bucket.delete_objects(
                    Delete={
                        'Objects': item
                    }
                )
        self._connection.s3client.delete_bucket(Bucket=self._uuid)

    def list_files(self):
        """List files in the bucket

        :rtype: list(s3.ObjectSummary)
        :returns: A list of ObjectSummary resources

        """
        bucket = self._connection.s3resource.Bucket(self._uuid)
        return bucket.objects.all()

    def directory(self, directory=''):
        """List files in a directory of the disk according to prefix.

        :rtype: list(s3.ObjectSummary)
        :returns: A list of ObjectSummary resources
        """
        bucket = self._connection.s3resource.Bucket(self._uuid)
        return bucket.objects.filter(Prefix=directory)

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
            directory += '/'

        filesdict = {}
        for root, dirs, files in os.walk(directory):
            for file_ in files:
                filepath = os.path.join(root, file_)
                name = filepath[len(directory):]
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

        class Comparable(object):
            def __init__(self, name_, e_tag, filepath_):
                self.name = name_
                self.e_tag = e_tag
                self.filepath = filepath_

            def __repr__(self):
                return "Name {0}, ETag {1}".format(self.name, self.e_tag)

            def __eq__(self, other):
                return self.name == other.name and self.e_tag == other.e_tag

            def __hash__(self):
                return hash(self.name) ^ hash(self.e_tag)

        def aws_md5sum(sourcepath):
            if os.stat(sourcepath).st_size < AWS_UPLOAD_MAX_SIZE:
                hash_md5 = hashlib.md5()
                with open(sourcepath, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                return "\"{0}\"".format(hash_md5.hexdigest())
            else:
                md5s = []
                with open(sourcepath, 'rb') as fp:
                    while True:

                        data = fp.read(AWS_UPLOAD_PART_SIZE)

                        if not data:
                            break
                        md5s.append(hashlib.md5(data))

                digests = b"".join(m.digest() for m in md5s)

                new_md5 = hashlib.md5(digests)
                new_etag = '"%s-%s"' % (new_md5.hexdigest(), len(md5s))
                return "\"{0}\"".format(new_etag)

        def localtocomparable(name_, filepath_):
            return Comparable(name_, aws_md5sum(filepath), filepath_)

        def objectsummarytocomparable(object_):
            return Comparable(object_.key, object_.e_tag, None)

        localfiles = []
        for name, filepath in files.items():
            localfiles.append(localtocomparable(name, filepath))

        local = set(localfiles)
        remotefiles = []
        for objectsummary in self.list_files():
            remotefiles.append(objectsummarytocomparable(objectsummary))

        remote = set(remotefiles)

        adds = local - remote
        removes = remote - local

        sadds = sorted(adds, key=lambda x: x.e_tag)
        groupedadds = [list(g) for _, g in itertools.groupby(
            sadds, lambda x: x.e_tag)]

        for file_ in removes:
            renames = [x for x in adds if x.e_tag == file_.e_tag]
            if len(renames) > 0:
                for dup in renames:
                    if verbose:
                        print("Copy", file_.name, "to", dup.name)
                    self.copy_file(file_.name, dup.name)
            if verbose:
                print("remove ", file_.name)
            self.delete_file(file_.name)

        remotefiles = []
        for objectsummary in self.list_files():
            remotefiles.append(objectsummarytocomparable(objectsummary))

        remote = set(remotefiles)

        for entry in groupedadds:
            try:
                rem = next(x for x in remote if x.e_tag == entry[0].e_tag)
                if rem.name == entry[0].name:
                    continue
                if verbose:
                    print("Link:", rem.name, "<-", entry[0].name)
                self.copy_file(rem.name, entry[0].name)
            except StopIteration:
                if verbose:
                    print("Upload:", entry[0].name)
                self.add_file(entry[0].filepath, entry[0].name)
            if len(entry) > 1:  # duplicate files
                for link in entry[1:]:
                    if not link.directory:
                        if verbose:
                            print("Link:", entry[0].name, "<-", link.name)
                        self.copy_file(entry[0].name, link.name)
                    else:
                        if verbose:
                            print("Add dir" + link.filepath + " " + str(link.name))
                        self.add_file(link.filepath, link.name)

    def add_file(self, local_or_file, remote=None):
        if isinstance(local_or_file, str):
            file_ = open(local_or_file, 'rb')
        else:
            file_ = local_or_file
        dest = remote or os.path.basename(file_.name)

        self._connection.s3client.upload_fileobj(file_, self._uuid, dest, Config=s3_multipart_config)
    add_file.__doc__ = storage.Storage.add_file.__doc__

    def get_all_files(self, output_dir, progress=None):
        return super(Bucket, self).get_all_files(output_dir, progress)
    get_all_files.__doc__ = storage.Storage.get_all_files.__doc__

    def get_file(self, remote, local=None, progress=None):
        return super(Bucket, self).get_file(remote, local, progress)
    get_file.__doc__ = storage.Storage.get_file.__doc__

    def add_directory(self, local, remote=""):
        if not os.path.isdir(local):
            raise IOError("Not a valid directory")
        if not remote.endswith('/'):
            remote += '/'
        for dirpath, _, files in os.walk(local):
            remote_loc = dirpath.replace(local, remote, 1)
            for filename in files:
                self.add_file(os.path.join(dirpath, filename),
                              posixpath.join(remote_loc, filename))
    add_directory.__doc__ = storage.Storage.add_directory.__doc__

    def copy_file(self, source, dest):
        copy_source = {
            'Bucket': self._uuid,
            'Key': source
        }
        return self._connection.s3client.copy(copy_source, self._uuid, dest, Config=s3_multipart_config)

    copy_file.__doc__ = storage.Storage.copy_file.__doc__

    def flush(self):
        pass
    flush.__doc__ = storage.Storage.flush.__doc__

    def update(self, flush=False):
        pass
    update.__doc__ = storage.Storage.update.__doc__

    def _download_file(self, remote, local, progress=None):
        with open(local, 'wb') as data:
            self._connection.s3client.download_fileobj(self._uuid, remote, data)
        return local

    def delete_file(self, remote):
        self._connection.s3client.delete_object(Bucket=self._uuid, Key=remote)
    delete_file.__doc__ = storage.Storage.delete_file.__doc__

    @property
    def uuid(self):
        """ Bucket identifier"""
        return self._uuid

    @property
    def description(self):
        """ Bucket identifier"""
        return self._uuid
