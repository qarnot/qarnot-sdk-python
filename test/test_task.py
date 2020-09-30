import pytest
import qarnot
from qarnot.task import Task
import datetime

class TestTaskProperties:
    class MockConnection:
        def none():
            return

    conn = MockConnection()

    def test_task_autodelete_default_value(self):
        task = Task(self.conn, "task-name")
        assert False == task.auto_delete

    def test_task_completion_ttl_default_value(self):
        task = Task(self.conn, "task-name")
        assert "00:00:00" == task.completion_ttl

    def test_task_autodelete_set_get(self):
        task = Task(self.conn, "task-name")
        task.auto_delete = False
        assert False == task.auto_delete
        task.auto_delete = True
        assert True == task.auto_delete

    def test_task_completion_ttl_set_get(self):
        task = Task(self.conn, "task-name")
        task.completion_ttl = datetime.timedelta(days=2, hours=33, minutes=66, seconds=66)
        assert "3.10:07:06" == task.completion_ttl
        task.completion_ttl = "4.11:08:06"
        assert "4.11:08:06" == task.completion_ttl

    def test_task_are_in_task_to_json(self):
        task = Task(self.conn, "task-name")
        task.completion_ttl = "4.11:08:06"
        task.auto_delete = True
        json_task = task._to_json()

        assert json_task['completionTimeToLive'] == '4.11:08:06'
        assert json_task['autoDeleteOnCompletion'] == True
