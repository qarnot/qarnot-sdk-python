import boto3
import botocore
import dateutil
import filecmp
import json
import os
import pytest
import requests
import requests_mock
import time

from boto3.s3.transfer import TransferConfig
from moto import mock_s3
from qarnot.bucket import Bucket
from qarnot.connection import Connection
from qarnot.exceptions import MissingDiskException, MissingTaskException, MaxDiskException, MaxTaskException, NotEnoughCreditsException, UnauthorizedException,BucketStorageUnavailableException
from qarnot.pool import Pool
from qarnot.task import Task
from qarnot.storage import Storage
from shutil import rmtree
from unittest.mock import Mock, MagicMock, PropertyMock, call, patch

def create_pool():
    return '{' \
        + '"name": "name",' \
        + '"profile": "docker-batch",' \
        + '"instanceCount": 1,' \
        + '"creationDate": "2018-09-22T15:45:23.0Z",' \
        + '"uuid": "12345678-1234-1234-1234-123456789123",' \
        + '"state": "Success"' \
        + '}'

@pytest.fixture(name="httpMock")
def create_http_mocker():
    with requests_mock.Mocker() as m:
        m.get("https://api.qarnot.com/settings",
            text='{"storage": "https://storage.qarnot.com"}')
        m.get("https://api.qarnot.com")
        m.get("https://api.qarnot.com/user",
            text='{"email": "fake.fakey@McFakey.pants",' \
            + '"diskCount": 0,' \
            + '"maxDisk": 200,' \
            + '"maxBucket": 0,' \
            + '"quotaBytesDisk": 203920,' \
            + '"quotaBytesBucket": 203920,' \
            + '"usedQuotaBytesDisk": 2000,' \
            + '"usedQuotaBytesBucket": 2000,' \
            + '"taskCount": 0,' \
            + '"maxTask": 200,' \
            + '"runningTaskCount": 0,' \
            + '"maxRunningTask": 10,' \
            + '"maxInstances": 20}')
        m.get("https://api.qarnot.com/info",
            text='{"email": "fake.fakey@McFakey.pants",' \
            + '"diskCount": 0,' \
            + '"maxDisk": 200,' \
            + '"maxBucket": 0,' \
            + '"quotaBytesDisk": 203920,' \
            + '"quotaBytesBucket": 203920,' \
            + '"usedQuotaBytesDisk": 2000,' \
            + '"usedQuotaBytesBucket": 2000,' \
            + '"taskCount": 0,' \
            + '"maxTask": 200,' \
            + '"runningTaskCount": 0,' \
            + '"maxRunningTask": 10,' \
            + '"maxInstances": 20}')
        yield m

                      
class TestConnection:
    @mock_s3
    def test_creation(self, httpMock):
        conn = Connection(client_token="token")

        assert conn.storage == "https://storage.qarnot.com"
        assert conn.cluster == "https://api.qarnot.com"
        assert conn.user_info.email == "fake.fakey@McFakey.pants"
        assert conn.user_info.disk_count == 0
        assert conn.user_info.max_disk == 200
        assert conn.user_info.max_bucket == 0
        assert conn.user_info.quota_bytes_disk == 203920
        assert conn.user_info.quota_bytes_bucket == 203920
        assert conn.user_info.used_quota_bytes_disk == 2000
        assert conn.user_info.used_quota_bytes_bucket == 2000
        assert conn.user_info.task_count == 0
        assert conn.user_info.max_task == 200
        assert conn.user_info.running_task_count == 0
        assert conn.user_info.max_running_task == 10
        assert conn.user_info.max_instances == 20

    @mock_s3
    def test_get_method(self, httpMock):
        httpMock.get("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=200)
        conn = Connection(client_token="token")
        response = conn._get("/message")
        assert response.status_code == 200 and response.json()["message"] == "Got it!"

    @mock_s3
    def test_get_method_unauthorized(self, httpMock):
        httpMock.get("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=401)
        conn = Connection(client_token="token")

        with pytest.raises(UnauthorizedException):
            response = conn._get("/message")
            assert response.status_code == 401 and response.json()["message"] == "Got it!"

    @mock_s3
    def test_patch_method_send_message(self, httpMock):
        httpMock.patch("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=200)
        conn = Connection(client_token="token")

        js = json.loads('{"message": "sent"}')
        response = conn._patch("/message", js)
        assert response.status_code == 200 and response.json()["message"] == "Got it!"
        assert httpMock.last_request.json()["message"] == "sent"

    @mock_s3
    def test_patch_method_unauthorized(self, httpMock):
        httpMock.patch("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=401)
        conn = Connection(client_token="token")

        with pytest.raises(UnauthorizedException):
            js = json.loads('{"message": "sent"}')
            response = conn._patch("/message", js)
            assert response.status_code == 401 and response.json()["message"] == "Got it!"
            assert httpMock.last_request.json()["message"] == "sent"

    @mock_s3
    def test_post_method_send_message(self, httpMock):
        httpMock.post("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=200)
        conn = Connection(client_token="token")

        js = json.loads('{"message": "sent"}')
        response = conn._post("/message", js)
        assert response.status_code == 200 and response.json()["message"] == "Got it!"
        assert httpMock.last_request.json()["message"] == "sent"

    @mock_s3
    def test_post_method_unauthorized(self, httpMock):
        httpMock.post("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=401)
        conn = Connection(client_token="token")

        with pytest.raises(UnauthorizedException):
            js = json.loads('{"message": "sent"}')
            response = conn._post("/message", js)
            assert response.status_code == 401 and response.json()["message"] == "Got it!"
            assert httpMock.last_request.json()["message"] == "sent"

    @mock_s3
    def test_delete_method(self, httpMock):
        httpMock.delete("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=200)
        conn = Connection(client_token="token")
        response = conn._delete("/message")
        assert response.status_code == 200 and response.json()["message"] == "Got it!"

    @mock_s3
    def test_delete_method_unauthorized(self, httpMock):
        httpMock.delete("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=401)
        conn = Connection(client_token="token")

        with pytest.raises(UnauthorizedException):
            response = conn._delete("/message")
            assert response.status_code == 401 and response.json()["message"] == "Got it!"

    @mock_s3
    def test_put_method_send_message(self, httpMock):
        httpMock.put("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=200)
        conn = Connection(client_token="token")

        js = json.loads('{"message": "sent"}')
        response = conn._put("/message", js)
        assert response.status_code == 200 and response.json()["message"] == "Got it!"
        assert httpMock.last_request.json()["message"] == "sent"

    @mock_s3
    def test_put_method_unauthorized(self, httpMock):
        httpMock.put("https://api.qarnot.com/message", text='{"message": "Got it!"}', status_code=401)
        conn = Connection(client_token="token")

        with pytest.raises(UnauthorizedException):
            js = json.loads('{"message": "sent"}')
            response = conn._put("/message", js)
            assert response.status_code == 401 and response.json()["message"] == "Got it!"
            assert httpMock.last_request.json()["message"] == "sent"

    @mock_s3
    def test_connection_user_info(self, httpMock):
        conn = Connection(client_token="token")
        user = conn.user_info

        assert httpMock.last_request.url == "https://api.qarnot.com/info"
        assert user.email == "fake.fakey@McFakey.pants"
        assert user.disk_count == 0
        assert user.max_disk == 200
        assert user.max_bucket == 0
        assert user.quota_bytes_disk == 203920
        assert user.quota_bytes_bucket == 203920
        assert user.used_quota_bytes_disk == 2000
        assert user.used_quota_bytes_bucket == 2000
        assert user.task_count == 0
        assert user.max_task == 200
        assert user.running_task_count == 0
        assert user.max_running_task == 10
        assert user.max_instances == 20

    @mock_s3
    def test_connection_get_buckets_with_no_s3_client(self, httpMock):
        conn = Connection(client_token="token")
        with pytest.raises(botocore.exceptions.ClientError):
            conn.buckets()

    @mock_s3
    def test_connection_get_buckets(self, httpMock):
        session = boto3.session.Session()
        client = session.client(service_name='s3',
                                aws_access_key_id="fake.fakey@McFakey.pants",
                                aws_secret_access_key="auth",
                                verify=True)
        resource = session.resource(service_name='s3',
                                    aws_access_key_id="fake.fakey@McFakey.pants",
                                    aws_secret_access_key="auth",
                                    verify=True)
        client.create_bucket(Bucket="bucket1")
        client.create_bucket(Bucket="bucket2")

        with patch('qarnot.connection.Connection.s3client', new_callable=PropertyMock) as mock_client:
            with patch('qarnot.connection.Connection.s3resource', new_callable=PropertyMock) as mock_resource:
                with patch('qarnot.connection.Connection.user_info', new_callable=PropertyMock):
                    mock_client.return_value = client
                    mock_resource.return_value = resource
                    conn = Connection(client_token="token")
                    conn._s3client = client
                    conn._s3resource = resource
                    buckets = list(map(lambda x: x._uuid, conn.buckets()))

                    assert "bucket1" in buckets and "bucket2" in buckets
    
    @mock_s3
    def test_connection_get_pools(self, httpMock):
        httpMock.get("https://api.qarnot.com/pools", text="{}")
        conn = Connection(client_token="token")
        conn.pools(False)

        assert httpMock.last_request.url == "https://api.qarnot.com/pools"

    @mock_s3
    def test_connection_get_pool_summaries(self, httpMock):
        httpMock.get("https://api.qarnot.com/pools/summaries", text="{}")
        conn = Connection(client_token="token")
        conn.pools()

        assert httpMock.last_request.url == "https://api.qarnot.com/pools/summaries"

    @mock_s3
    def test_connection_get_tasks(self, httpMock):
        httpMock.get("https://api.qarnot.com/tasks", text="{}")
        conn = Connection(client_token="token")
        conn.tasks(summary=False)

        assert httpMock.last_request.url == "https://api.qarnot.com/tasks"

    @mock_s3
    def test_connection_get_tasks_summaries(self, httpMock):
        httpMock.get("https://api.qarnot.com/tasks/summaries", text="{}")
        conn = Connection(client_token="token")
        conn.tasks(summary=True)

        assert httpMock.last_request.url == "https://api.qarnot.com/tasks/summaries"

    @mock_s3
    def test_connection_retieve_pool(self, httpMock):
        httpMock.get(
            "https://api.qarnot.com/pools/12345678-1234-1234-1234-123456789123",
            text=create_pool())
        conn = Connection(client_token="token")
        conn.retrieve_pool("12345678-1234-1234-1234-123456789123")

        assert httpMock.last_request.url == "https://api.qarnot.com/pools/12345678-1234-1234-1234-123456789123"
