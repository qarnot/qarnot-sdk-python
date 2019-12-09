import json
import pytest
import requests

from pytest_mock import mocker
from qarnot.connection import Connection
from qarnot.pool import Pool
from qarnot.task import Task
from unittest.mock import Mock, MagicMock, call

class TestTask:
    def test_create_task(self):
        task = Task(None, "name", "docker-batch", 1)
        assert task.name == "name" and task.profile == "docker-batch" and task.instancecount == 1
    
    def test_create_task_with_pool(self):
        mock = Mock(Pool)
        mock.uuid = '00000000-0000-0000-0000-123456789123'

        task = Task(None, "name", mock, 1)
        assert task.name == "name" and task._pooluuid == "00000000-0000-0000-0000-123456789123" and task.instancecount

    def test_task_retreive(self):
        response = requests.Response()
        response.status_code = 200
        response.json = MagicMock()
        response.json.return_value = json.loads('{"name": "name","profile": "docker-batch","instanceCount": 1,"shortname":"name", "poolUuid": null, "resourceBuckets": null, "resultBucket":null, "status": null, "creationDate": "2018-06-13T09:06:20Z", "errors": [], "constants": [],"uuid": "00000000-0000-0000-0000-000000000000", "state": "yes"}')

        mock = Mock(Connection)
        mock._get.return_value = response

        Task._retrieve(mock, "00000000-0000-0000-0000-123456789123")
        Task.from_json = MagicMock()
        Task.from_json.return_value = Task(mock, "name", "docker-batch", 1)
        mock._get.assert_called_with("/tasks/00000000-0000-0000-0000-123456789123")

    def test_task_run(self):
        mockconn = Mock(Connection)
        task = Task(mockconn, "name", "docker-batch", 1)

        mock = Mock(task)
        
        mock.run()
        calls = [call(task.submit), call(task.wait)]
        mock.assert_has_calls(calls)



