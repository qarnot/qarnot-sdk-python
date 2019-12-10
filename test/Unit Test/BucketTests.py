import boto3
import botocore
import dateutil
import json
import os
import pytest
import requests
import requests_mock
import time

from moto import mock_s3
from qarnot.bucket import Bucket
from qarnot.connection import Connection
from qarnot.exceptions import MissingDiskException, MissingTaskException, MaxDiskException, MaxTaskException, NotEnoughCreditsException
from qarnot.pool import Pool
from qarnot.task import Task
from qarnot.storage import Storage
from unittest.mock import Mock, MagicMock, PropertyMock, call, patch


@mock_s3
class TestBucket:

    # Need to find how to put massive connection creation in something like a setup

    def test_create_bucket(self):
        with requests_mock.Mocker() as m:
            m.get("https://api.qarnot.com/settings", text='{"storage": "https://storage.qarnot.com"}')
            m.get("https://api.qarnot.com")
            m.get("https://api.qarnot.com/user", text='{"email": "fake.fakey@McFakey.pants"}')
            m.get("https://api.qarnot.com/info", text='{"email": "fake.fakey@McFakey.pants"}')
            session = boto3.session.Session()
            client = session.client(service_name='s3',
                                            aws_access_key_id="fake.fakey@McFakey.pants",
                                            aws_secret_access_key="auth",
                                            verify=True)
            resource = session.resource(service_name='s3',
                                                aws_access_key_id="fake.fakey@McFakey.pants",
                                                aws_secret_access_key="auth",
                                                verify=True)
            with patch('qarnot.connection.Connection.s3client', new_callable=PropertyMock) as mock_client:
                with patch('qarnot.connection.Connection.user_info', new_callable=PropertyMock):
                    mock_client.return_value = client
                    connection = Connection(client_token="token")
                    bucket = Bucket(connection, "bucket")

                    response = connection.s3client.list_buckets()

                    assert bucket._uuid == "bucket" and len(
                        response["Buckets"]) == 1 and response["Buckets"][0]['Name'] == "bucket"
