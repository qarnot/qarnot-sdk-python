import datetime
import pytest

from qarnot.task import Task

from .mock_connection import MockConnection, PostRequest


@pytest.fixture(name="mock_conn")
def mock_conn_fixture():
    return MockConnection()


class TestTaskProperties:
    def test_task_autodelete_default_value(self, mock_conn):
        task = Task(mock_conn, "task-name")
        assert task.auto_delete is False

    def test_task_completion_ttl_default_value(self, mock_conn):
        task = Task(mock_conn, "task-name")
        assert "00:00:00" == task.completion_ttl

    def test_task_autodelete_set_get(self, mock_conn):
        task = Task(mock_conn, "task-name")
        task.auto_delete = False
        assert task.auto_delete is False
        task.auto_delete = True
        assert task.auto_delete is True

    def test_task_completion_ttl_set_get(self, mock_conn):
        task = Task(mock_conn, "task-name")
        task.completion_ttl = datetime.timedelta(days=2, hours=33, minutes=66, seconds=66)
        assert "3.10:07:06" == task.completion_ttl
        task.completion_ttl = "4.11:08:06"
        assert "4.11:08:06" == task.completion_ttl

    def test_task_are_in_task_to_json(self, mock_conn):
        task = Task(mock_conn, "task-name")
        task.completion_ttl = "4.11:08:06"
        task.auto_delete = True
        json_task = task._to_json()  # pylint: disable=protected-access

        assert json_task['completionTimeToLive'] == '4.11:08:06'
        assert json_task['autoDeleteOnCompletion'] is True
