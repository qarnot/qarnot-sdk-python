import copy
import datetime
from io import StringIO
import sys
import uuid
import pytest
from qarnot.retry_settings import RetrySettings

from qarnot.task import Task
from qarnot.privileges import Privileges
from qarnot.bucket import Bucket
from qarnot.advanced_bucket import BucketPrefixFiltering, PrefixResourcesTransformation
import datetime

from .mock_connection import MockConnection, MockResponse
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
        ("privileges", Privileges()),
    ])
    def test_task_property_default_value(self, mock_conn, property_name,  expected_value):
        task = Task(mock_conn, "task-name")
        assert getattr(task, property_name) == expected_value

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
        ("privileges", Privileges()),
    ])
    def test_task_property_update_value(self, mock_conn, property_name,  expected_value):
        task = Task(mock_conn, "task-name")
        task._update(default_json_task)
        assert getattr(task, property_name) == expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("name", default_json_task["name"]),
        ("privileges", default_json_task["privileges"]),
        ("retrySettings", default_json_task["retrySettings"]),
    ])
    def test_task_property_send_to_json_representation(self, mock_conn, property_name, expected_value):
        task = Task(mock_conn, "task-name")
        task._update(default_json_task)
        task_json = task._to_json()
        assert task_json[property_name] == expected_value

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
            },
            "cacheTTLSec": 1000
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
        assert 1000 == task.resources[0]._cache_ttl_sec


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

    def test_task_privileges(self, mock_conn):
        task = Task(mock_conn, "task-name")
        task.allow_credentials_to_be_exported_to_task_environment()
        assert task.privileges is not None
        assert task.privileges._exportApiAndStorageCredentialsInEnvironment == True

        json_task = task._to_json()
        assert json_task['privileges'] is not None
        assert json_task['privileges']['exportApiAndStorageCredentialsInEnvironment'] is True

        # fields that need to be non null for the deserialization to not fail
        json_task['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_task['uuid'] = str(uuid.uuid4())
        json_task['state'] = 'Submitted'
        json_task['runningCoreCount'] = 0
        json_task['runningInstanceCount'] = 0

        pool_from_json = Task(mock_conn, "task-name")
        pool_from_json._update(json_task)
        assert pool_from_json.privileges is not None
        assert pool_from_json.privileges._exportApiAndStorageCredentialsInEnvironment is True

    def test_task_retry_settings(self, mock_conn):
        task = Task(mock_conn, "task-name")

        json_task = task._to_json()
        assert json_task['retrySettings'] is not None
        assert json_task['retrySettings']['maxTotalRetries'] is None
        assert json_task['retrySettings']['maxPerInstanceRetries'] is None

        task.retry_settings = RetrySettings(36, 12)
        json_task = task._to_json()
        assert json_task['retrySettings'] is not None
        assert json_task['retrySettings']['maxTotalRetries'] is 36
        assert json_task['retrySettings']['maxPerInstanceRetries'] is 12

        # fields that need to be non null for the deserialization to not fail
        json_task['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_task['uuid'] = str(uuid.uuid4())
        json_task['state'] = 'Submitted'
        json_task['runningCoreCount'] = 0
        json_task['runningInstanceCount'] = 0

        pool_from_json = Task(mock_conn, "task-name")
        pool_from_json._update(json_task)
        assert pool_from_json.retry_settings is not None
        assert pool_from_json.retry_settings._maxTotalRetries is 36
        assert pool_from_json.retry_settings._maxPerInstanceRetries is 12

    # WARNING: this test last at least 80s because task.wait() wait for 10s between each update calls and the task go through 8 different states
    # To make the test faster some states can be removed (the 7 first states are all the states that correspond to a non complete task and keep
    # the wait alive. The last state is one of the final status that stop the wait function)
    # NOTE: Some of the states have been commented out and removed from the test to make it quicker (see comment above).
    def test_task_wait_can_print_updated_state_stdout_stderr(self, mock_conn: MockConnection):
        # Redirect standard output and error for assertions
        capturedOutput = StringIO()
        sys.stdout = capturedOutput
        capturedStderr = StringIO()
        sys.stderr = capturedStderr

        # Mock the responses for task update
        task = Task(mock_conn, "task-name")
        task_json = copy.deepcopy(default_json_task)
        task_json.update({
            "state":  'Submitted',
            "previousState":  None,
        })
        task._update(task_json)
        last_State = 'Submitted'
        i = 0
        mock_conn.add_response(MockResponse(200, task_json))
        states = [
            #'PartiallyDispatched',
            #'FullyDispatched',
            #'PartiallyExecuting',
            'FullyExecuting',
            #'DownloadingResults',
            #'UploadingResults',
            'Success']
        for new_state in states:

            # Update task stdout
            stdout_json = "stdout %s" % i
            mock_conn.add_response(MockResponse(200, stdout_json))

            # Update task stderr
            stderr_json = "stderr %s" % i
            mock_conn.add_response(MockResponse(200, stderr_json))

            # Update task state
            task_json = copy.deepcopy(default_json_task)
            task_json.update({
                "state":  new_state,
                "previousState":  last_State,
            })
            mock_conn.add_response(MockResponse(200, task_json))
            last_State = new_state

            # keep same stdout for the second check after the update
            stdout_json = "stdout %s" % i
            mock_conn.add_response(MockResponse(200, stdout_json))

            # keep same stderr for the second check after the update
            stderr_json = "stderr %s" % i
            mock_conn.add_response(MockResponse(200, stderr_json))

            i += 1
        mock_conn.add_response(MockResponse(200, default_json_task))

        # Wait with calls to get and print the task progress
        task.wait(follow_state=True, follow_stdout=True, follow_stderr=True)

        # Reset redirections
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        output = capturedOutput.getvalue()
        assert output is not None, "the output should contain task update output"
        stderr = capturedStderr.getvalue()
        assert stderr is not None, "the stderr should contain task update stderr"
        for state in states:
            assert state in output, "All state updates should be printed on stdout"
        for i in range(0,len(states)):
            assert "stdout %s" % i in output, "All task stdout should be printed to user stdout"
            assert "stderr %s" % i in stderr, "All task stderr should be printed to user stderr"
