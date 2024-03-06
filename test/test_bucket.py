import boto3
import hashlib
import os.path
import qarnot

from pathlib import Path
from qarnot.bucket import Bucket
from unittest import TestCase
from unittest.mock import patch, Mock

try:
    from moto import mock_aws
except ImportError:
    from moto import mock_s3 as mock_aws

from qarnot.exceptions import MissingBucketException



def mock_connection_base(mock_s3buckets=None):
    mock_connection = Mock({'other.side_effect': KeyError})
    mock_connection.s3client = Mock()
    mock_connection.s3resource = Mock()
    mock_connection.s3resource.Bucket.return_value = mock_s3buckets
    mock_connection._sanitize_bucket_paths = True
    mock_connection._show_bucket_warnings = True
    return mock_connection


class TestBucketPublicMethods(TestCase):
    def test_init_bucket(self):
        mock_connection = mock_connection_base()
        bucket = Bucket(mock_connection, "name", True)
        mock_connection.s3client.create_bucket.assert_called_once()

    @patch("qarnot.bucket.Bucket.add_file")
    def test_bucket_add_string(self, add_file):
        bucket = qarnot.bucket.Bucket(mock_connection_base(), "bucket_name", False)
        string_to_send = "Test string to be send"
        remote_path = "path/to/go"

        bucket.add_string(string_to_send, remote_path)
        add_file.assert_called_once()
        args = add_file.call_args[0]
        assert args[0].read() == string_to_send.encode('utf-8')
        assert args[1] == remote_path


# ================================== Utils functions ==================================
def write_in(path, text):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, 'w+') as the_file:
        the_file.write(text)


def compute_etag(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return '%s' % hash_md5.hexdigest()


# Returns a set containing the couple (filename, etag) for every file in a given folder
def list_local_files(path):
    set_of_filenames = set()
    for root, _, files in os.walk(path):
        for file_name in files:
            relative_file_path = Path(os.path.join(root, file_name)).relative_to(path).as_posix()
            set_of_filenames.add((relative_file_path, compute_etag(os.path.join(root, file_name))))
    return set_of_filenames


# This is just to keep track of how many times the copy_file method was called
class BucketWithCopyCounter(Bucket):
    def __init__(self, connection, name, create=True):
        super().__init__(connection, name, create)
        self._nbr_of_copies = 0

    def copy_file(self, source, dest):
        self._nbr_of_copies += 1
        super().copy_file(source, dest)


# ================================== Tests using Moto ==================================
class TestBucketPublicMethodsMoto:

    @mock_aws
    def test_sync_files_avoid_unnecessary_copies(self, tmp_path):
        # cf QNET-5274
        bucket_name = "dolly"

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Add 2 identical files in the bucket by our own way
        bucket = BucketWithCopyCounter(q_conn, bucket_name, True)
        bucket.add_string("Tu ne copieras point sur ton voisin", "remote1")
        bucket.add_string("Tu ne copieras point sur ton voisin", "remote2")

        # Write some files with identical content in a temporary folder
        write_in(tmp_path / "local1", 'Tu ne copieras point sur ton voisin')
        write_in(tmp_path / "local2", 'Tu ne copieras point sur ton voisin')

        # Synchronize the content of this folder with the bucket
        bucket.sync_directory(tmp_path.as_posix())

        # Check that it's indeed synchronized
        local_files = list_local_files(tmp_path)
        bucket_files = set()
        for file in bucket.list_files():
            bucket_files.add((file.key, file.e_tag.strip('"')))
        assert local_files == bucket_files, "Bucket and local folder have different content whereas they should be " \
                                            "identical "

        # Check that there were no unnecessary copies performed
        assert bucket._nbr_of_copies == 2, "The copy method should have been called only twice\
                                            ({} calls here)".format(bucket._nbr_of_copies)

class TestBucketExceptionHandling(TestCase):

    @mock_aws
    def test_missing_bucket_at_deletion(self):

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Create bucket object from qarnot api and ensure s3 bucket is created
        bucket = Bucket(q_conn, "delete-bucket-test", True)
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is not None

        # Delete bucket and ensure is removed from s3
        bucket.delete()
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is None

        # Ensure deletion of a missing bucket raises the appropriate exception
        with self.assertRaises(MissingBucketException):
            bucket.delete()

    @mock_aws
    def test_missing_bucket_when_adding_file(self):

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Create bucket object from qarnot api and ensure s3 bucket is created
        bucket = Bucket(q_conn, "delete-bucket-test", True)
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is not None

        # Delete bucket and ensure is removed from s3
        bucket.delete()
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is None

        # Ensure trying to add file of a missing bucket raises the appropriate exception
        with self.assertRaises(MissingBucketException):
            bucket.add_string("ost in the vacuum", "remote")
        with open("fileToAdd", "w") as f:
            with self.assertRaises(MissingBucketException):
                bucket.add_file(f.name, "remote")
        os.remove("fileToAdd")

    @mock_aws
    def test_missing_bucket_when_listing_or_downloading_files(self):

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Create bucket object from qarnot api and ensure s3 bucket is created
        bucket = Bucket(q_conn, "delete-bucket-test", True)
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is not None

        # Delete bucket and ensure is removed from s3
        bucket.delete()
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is None

        # Ensure trying to get files of a missing bucket raises the appropriate exception
        with self.assertRaises(MissingBucketException):
            bucket.get_all_files("")
        with self.assertRaises(MissingBucketException):
            bucket.list_files()

    @mock_aws
    def test_missing_bucket_when_downloading_file(self):

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Create bucket object from qarnot api and ensure s3 bucket is created
        bucket = Bucket(q_conn, "delete-bucket-test", True)
        bucket.add_string("Je vais perdre la bucktête", "remote")
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is not None

        # Delete bucket and ensure is removed from s3
        bucket.delete()
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is None

        # Ensure trying to get file of a missing bucket raises the appropriate exception
        with self.assertRaises(MissingBucketException):
            bucket.get_file("remote")

    @mock_aws
    def test_missing_bucket_when_copying_file(self):

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Create bucket object from qarnot api and ensure s3 bucket is created
        bucket = Bucket(q_conn, "delete-bucket-test", True)
        bucket.add_string("Je vais perdre la bucktête", "remote")
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is not None

        # Delete bucket and ensure is removed from s3
        bucket.delete()
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is None

        # Ensure trying to get file of a missing bucket raises the appropriate exception
        with self.assertRaises(MissingBucketException):
            bucket.copy_file("remote", "destination")

    @mock_aws
    def test_missing_bucket_when_syncing_files(self):

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Create bucket object from qarnot api and ensure s3 bucket is created
        bucket = Bucket(q_conn, "delete-bucket-test", True)
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is not None

        # Delete bucket and ensure is removed from s3
        bucket.delete()
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is None

        # Ensure syncing of files in a missing bucket raises the appropriate exception
        with open("newFile", "w") as f:
            files = {}
            files[f.name] = f.name
            with self.assertRaises(MissingBucketException):
                bucket.sync_files(files)

    @mock_aws
    def test_missing_bucket_at_file_deletion(self):

        # Mock S3 client and resource
        q_conn = mock_connection_base()
        q_conn.s3client = boto3.client("s3")
        q_conn.s3resource = boto3.resource('s3')

        # Create bucket object from qarnot api and ensure s3 bucket is created
        bucket = Bucket(q_conn, "delete-bucket-test", True)
        bucket.add_string("Je vais perdre la bucktête", "remote")
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is not None

        # Delete bucket and ensure is removed from s3
        bucket.delete()
        s3bucket = q_conn.s3resource.Bucket(bucket._uuid)
        assert s3bucket.creation_date is None

        # Ensure deletion of a missing bucket raises the appropriate exception
        with self.assertRaises(MissingBucketException):
            bucket.delete_file("remote")
