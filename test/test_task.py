import datetime
import pytest

from qarnot.task import Task
from qarnot.bucket import Bucket
from qarnot.advanced_bucket import BucketPrefixFiltering, PrefixResourcesTransformation
import datetime

from .mock_connection import MockConnection
from .mock_task import default_json_task, task_with_running_instances

@pytest.fixture(name="mock_conn")
def mock_conn_fixture():
    return MockConnection()


class TestTaskProperties:
    def submit_task(self, task):
        task._uuid = "set"

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

    @pytest.mark.parametrize("property_name, expected_value", [
        ("previous_state", None),
        ("state_transition_time", None),
        ("previous_state_transition_time", None),
        ("last_modified", None),
        ("snapshot_interval", None),
        ("progress", None),
        ("execution_time", None),
        ("wall_time", None),
        ("end_date", None),
    ])
    def test_task_property_default_value(self, mock_conn, property_name,  expected_value):
        task = Task(mock_conn, "task-name")
        assert getattr(task, property_name) is expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("previous_state", default_json_task["previousState"]),
        ("state_transition_time", default_json_task["stateTransitionTime"]),
        ("previous_state_transition_time", default_json_task["previousStateTransitionTime"]),
        ("last_modified", default_json_task["lastModified"]),
        ("snapshot_interval", default_json_task["snapshotInterval"]),
        ("progress", default_json_task["progress"]),
        ("execution_time", default_json_task["executionTime"]),
        ("wall_time", default_json_task["wallTime"]),
        ("end_date", default_json_task["endDate"]),
    ])
    def test_task_property_update_value(self, mock_conn, property_name,  expected_value):
        task = Task(mock_conn, "task-name")
        task._update(default_json_task)
        assert getattr(task, property_name) is expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("name", default_json_task["name"]),
    ])
    def test_task_property_send_to_json_representation(self, mock_conn, property_name, expected_value):
        task = Task(mock_conn, "task-name")
        task._update(default_json_task)
        task_json = task._to_json()
        assert task_json[property_name] is expected_value

    @pytest.mark.parametrize("property_name, set_value, expected_value", [
        ("name", "name", "name")
    ])
    def test_task_set_property_value(self, mock_conn, property_name, set_value, expected_value):
        task = Task(mock_conn, "task-name")
        setattr(task, property_name, set_value)
        assert getattr(task, property_name) == expected_value

    @pytest.mark.parametrize("property_name, set_value, exception", [
        ("uuid", "error-can-set-uuid", AttributeError)
    ])
    def test_task_set_forbidden_property_raise_exception(self, mock_conn, property_name, set_value, exception):
        task = Task(mock_conn, "task-name")
        with pytest.raises(exception):
            setattr(task, property_name, set_value)

    @pytest.mark.parametrize("property_name, set_value, exception", [
        ("instancecount", 5, AttributeError)
    ])
    def test_task_set_property_raise_exception_after_submitted(self, mock_conn, property_name, set_value, exception):
        task = Task(mock_conn, "task-name")
        self.submit_task(task)
        with pytest.raises(exception):
            setattr(task, property_name, set_value)

    def test_advance_bucket_in_task_to_json(self, mock_conn):
        task = Task(mock_conn, "task-name", "profile")
        bucket = Bucket(mock_conn, "name", False)
        bucket2 = bucket.with_filtering(BucketPrefixFiltering(
            "prefix1")).with_resource_transformation(PrefixResourcesTransformation("prefix2"))

        task.resources.append(bucket2)
        json_task = task._to_json()
        json_bucket = json_task["advancedResourceBuckets"][0]
        assert "name" == json_bucket["bucketName"]
        assert "prefix1" == json_bucket["filtering"]["prefixFiltering"]["prefix"]
        assert "prefix2" == json_bucket["resourcesTransformation"]["stripPrefix"]["prefix"]

    def test_bucket_in_task_from_json(self, mock_conn):
        json_bucket = "bucket-name"
        json_task = {
            "name": "taskName",
            "shortname": "taskShortname",
            "profile": "profile",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "resourceBuckets": [json_bucket],
            "creationDate": "2019-11-08T10:54:11Z",
            "uuid": "000",
            "state": "Submitted",
        }
        task = Task.from_json(mock_conn, json_task)
        task._auto_update = False
        assert "bucket-name" == task.resources[0].uuid

    def test_advance_bucket_in_task_from_json(self, mock_conn):
        json_bucket = {
            "bucketName": "name",
            "filtering": {
                "prefixFiltering": {
                    "prefix": "prefix1"
                }
            },
            "resourcesTransformation": {
                "stripPrefix": {
                    "prefix": "prefix2"
                }
            }
        }
        json_task = {
            "name": "taskName",
            "shortname": "taskShortname",
            "profile": "profile",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "advancedResourceBuckets": [json_bucket],
            "creationDate": "2019-11-08T10:54:11Z",
            "uuid": "000",
            "state": "Submitted",
        }
        task = Task.from_json(mock_conn, json_task)
        task._auto_update = False

        assert "name" == task.resources[0].uuid
        assert "prefix1" == task.resources[0]._filtering._filters["prefixFiltering"].prefix
        assert "prefix2" == task.resources[0]._resources_transformation._resource_transformers["stripPrefix"].prefix


    def test_execution_attempt_count_in_running_instances(self, mock_conn):
        task = Task(mock_conn, "task-name")
        task._update(task_with_running_instances)
        assert len(task.status.running_instances_info.per_running_instance_info) == 2
        assert task.status.running_instances_info.per_running_instance_info[0].execution_attempt_count == 1
        assert task.status.running_instances_info.per_running_instance_info[1].execution_attempt_count == 2


    def test_execution_attempt_count_in_completed_instances(self, mock_conn):
        task = Task(mock_conn, "task-name")
        task._update(default_json_task)
        assert task.completed_instances[0].execution_attempt_count == 43
