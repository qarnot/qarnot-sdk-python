from unittest import mock, TestCase
import pytest
import qarnot
from qarnot.pool import Pool
from qarnot.bucket import Bucket
import datetime

from unittest.mock import patch, mock_open, Mock, MagicMock, PropertyMock
import os.path
import boto3

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
