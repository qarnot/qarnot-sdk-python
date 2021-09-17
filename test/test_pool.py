import pytest
import qarnot
from qarnot.pool import Pool
from qarnot.bucket import Bucket
from qarnot.advanced_bucket import BucketPrefixFiltering, PrefixResourcesTransformation
import datetime
from .mock_connection import MockConnection, PatchRequest, none_function
from .mock_pool import default_json_pool


class TestPoolProperties:
    def submit_pool(self, pool):
        pool._uuid = "set"

    conn = MockConnection()
    def test_pool_autodelete_default_value(self):
        pool = Pool(self.conn, "pool-name", "profile")
        assert False == pool.auto_delete

    def test_pool_completion_ttl_default_value(self):
        pool = Pool(self.conn, "pool-name", "profile")
        assert "00:00:00" == pool.completion_ttl

    def test_pool_autodelete_set_get(self):
        pool = Pool(self.conn, "pool-name", "profile")
        pool.auto_delete = False
        assert False == pool.auto_delete
        pool.auto_delete = True
        assert True == pool.auto_delete

    def test_pool_completion_ttl_set_get(self):
        pool = Pool(self.conn, "pool-name", "profile")
        pool.completion_ttl = datetime.timedelta(days=2, hours=33, minutes=66, seconds=66)
        assert "3.10:07:06" == pool.completion_ttl
        pool.completion_ttl = "4.11:08:06"
        assert "4.11:08:06" == pool.completion_ttl

    def test_pool_are_in_pool_to_json(self):
        pool = Pool(self.conn, "pool-name", "profile")
        pool.completion_ttl = "4.11:08:06"
        pool.auto_delete = True
        json_pool = pool._to_json()

        assert json_pool['completionTimeToLive'] == '4.11:08:06'
        assert json_pool['autoDeleteOnCompletion'] == True

    def test_update_resources_send_the_good_url(self):
        update_connection = MockConnection()
        pool = Pool(update_connection, "pool-name", "profile")
        pool._uuid = "uuid"
        pool.update = none_function
        pool.update_resources()
        assert type(update_connection.requests[0]) == PatchRequest
        assert update_connection.requests[0].uri == "/pools/uuid"

    @pytest.mark.parametrize("property_name, expected_value", [
        ("previous_state", None),
        ("state_transition_time", None),
        ("previous_state_transition_time", None),
        ("last_modified", None),
        ("execution_time", None),
        ("end_date", None),
        ("tasks_default_wait_for_pool_resources_synchronization", False),
    ])
    def test_pool_property_default_value(self, property_name,  expected_value):
        pool = Pool(self.conn, "pool-name", "profile")
        assert getattr(pool, property_name) is expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("previous_state", default_json_pool["previousState"]),
        ("state_transition_time", default_json_pool["stateTransitionTime"]),
        ("previous_state_transition_time", default_json_pool["previousStateTransitionTime"]),
        ("last_modified", default_json_pool["lastModified"]),
        ("execution_time", default_json_pool["executionTime"]),
        ("end_date", default_json_pool["endDate"]),
        ("tasks_default_wait_for_pool_resources_synchronization", default_json_pool["taskDefaultWaitForPoolResourcesSynchronization"]),
    ])
    def test_pool_property_update_value(self, property_name,  expected_value):
        pool = Pool(self.conn, "pool-name", "profile")
        pool._update(default_json_pool)
        assert getattr(pool, property_name) is expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("taskDefaultWaitForPoolResourcesSynchronization", default_json_pool["taskDefaultWaitForPoolResourcesSynchronization"]),
    ])
    def test_pool_property_send_to_json_representation(self, property_name, expected_value):
        pool = Pool(self.conn, "pool-name", "profile")
        pool._update(default_json_pool)
        pool_json = pool._to_json()
        assert pool_json[property_name] is expected_value

    @pytest.mark.parametrize("property_name, set_value, expected_value", [
        ("name", "name", "name")
    ])
    def test_pool_set_property_value(self, property_name, set_value, expected_value):
        pool = Pool(self.conn, "pool-name", "profile")
        setattr(pool, property_name, set_value)
        assert getattr(pool, property_name) == expected_value

    @pytest.mark.parametrize("property_name, set_value, exception", [
        ("uuid", "error-can-set-uuid", AttributeError)
    ])
    def test_pool_set_forbidden_property_raise_exception(self, property_name, set_value, exception):
        pool = Pool(self.conn, "pool-name", "profile")
        with pytest.raises(exception):
            setattr(pool, property_name, set_value)

    @pytest.mark.parametrize("property_name, set_value, exception", [
        ("instancecount", 5, AttributeError)
    ])
    def test_pool_set_property_raise_exception_after_submitted(self, property_name, set_value, exception):
        pool = Pool(self.conn, "pool-name", "profile")
        self.submit_pool(pool)
        with pytest.raises(exception):
            setattr(pool, property_name, set_value)

    def test_advance_bucket_in_pool_to_json(self):
        pool = Pool(self.conn, "pool-name", "profile")
        bucket = Bucket(self.conn, "name", False)
        bucket2 = bucket.with_filtering(BucketPrefixFiltering(
            "prefix1")).with_resource_transformation(PrefixResourcesTransformation("prefix2"))

        pool.resources.append(bucket2)
        json_pool = pool._to_json()
        json_bucket = json_pool["advancedResourceBuckets"][0]
        assert "name" == json_bucket["bucketName"]
        assert "prefix1" == json_bucket["filtering"]["prefixFiltering"]["prefix"]
        assert "prefix2" == json_bucket["resourcesTransformation"]["stripPrefix"]["prefix"]

    def test_bucket_in_pool_from_json(self):
        json_bucket = "bucket-name"
        json_pool = {
            "name": "poolName",
            "shortname": "poolShortname",
            "profile": "profile",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "resourceBuckets": [json_bucket],
            "creationDate": "2019-11-08T10:54:11Z",
            "uuid": "000",
            "state": "Submitted",
        }
        pool = Pool.from_json(self.conn, json_pool)
        pool._auto_update = False
        assert "bucket-name" == pool.resources[0].uuid

    def test_advance_bucket_in_pool_from_json(self):
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
        json_pool = {
            "name":"poolName",
            "shortname":"poolShortname",
            "profile": "profile",
            "instanceCount": 1,
            "runningCoreCount": None,
            "runningInstanceCount": None,
            "advancedResourceBuckets": [json_bucket],
            "creationDate": "2019-11-08T10:54:11Z",
            "uuid": "000",
            "state": "Submitted",
        }
        pool = Pool.from_json(self.conn, json_pool)
        pool._auto_update = False

        assert "name" == pool.resources[0].uuid
        assert "prefix1" == pool.resources[0]._filtering._filters["prefixFiltering"].prefix
        assert "prefix2" == pool.resources[0]._resources_transformation._resource_transformers["stripPrefix"].prefix
