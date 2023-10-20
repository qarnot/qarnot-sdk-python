import uuid
import pytest
import qarnot
from qarnot.forced_network_rule import ForcedNetworkRule
from qarnot.pool import Pool
from qarnot.privileges import Privileges
from qarnot.bucket import Bucket
from qarnot.advanced_bucket import BucketPrefixFiltering, PrefixResourcesTransformation
import datetime

from qarnot.privileges import Privileges
from qarnot.retry_settings import RetrySettings
from qarnot.scheduling_type import FlexScheduling, OnDemandScheduling, ReservedScheduling
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
        ("privileges", Privileges()),
    ])
    def test_pool_property_default_value(self, property_name,  expected_value):
        pool = Pool(self.conn, "pool-name", "profile")
        assert getattr(pool, property_name) == expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("previous_state", default_json_pool["previousState"]),
        ("state_transition_time", default_json_pool["stateTransitionTime"]),
        ("previous_state_transition_time", default_json_pool["previousStateTransitionTime"]),
        ("last_modified", default_json_pool["lastModified"]),
        ("execution_time", default_json_pool["executionTime"]),
        ("end_date", default_json_pool["endDate"]),
        ("tasks_default_wait_for_pool_resources_synchronization", default_json_pool["taskDefaultWaitForPoolResourcesSynchronization"]),
        ("privileges", Privileges()),
    ])
    def test_pool_property_update_value(self, property_name,  expected_value):
        pool = Pool(self.conn, "pool-name", "profile")
        pool._update(default_json_pool)
        assert getattr(pool, property_name) == expected_value

    @pytest.mark.parametrize("property_name, expected_value", [
        ("taskDefaultWaitForPoolResourcesSynchronization", default_json_pool["taskDefaultWaitForPoolResourcesSynchronization"]),
        ("privileges", default_json_pool["privileges"]),
        ("defaultRetrySettings", default_json_pool["defaultRetrySettings"]),
    ])
    def test_pool_property_send_to_json_representation(self, property_name, expected_value):
        pool = Pool(self.conn, "pool-name", "profile")
        pool._update(default_json_pool)
        pool_json = pool._to_json()
        assert pool_json[property_name] == expected_value

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
            },
            "cacheTTLSec": 1000
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
        assert 1000 == pool.resources[0]._cache_ttl_sec

    def test_pool_privileges(self):
        pool = Pool(self.conn, "pool-name", "profile")
        pool.allow_credentials_to_be_exported_to_pool_environment()
        assert pool.privileges is not None
        assert pool.privileges._exportApiAndStorageCredentialsInEnvironment == True

        json_pool = pool._to_json()
        assert json_pool['privileges'] is not None
        assert json_pool['privileges']['exportApiAndStorageCredentialsInEnvironment'] is True

        # fields that need to be non null for the deserialization to not fail
        json_pool['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_pool['uuid'] = str(uuid.uuid4())
        json_pool['state'] = 'Submitted'

        pool_from_json = Pool(self.conn, "pool-name", "profile")
        pool_from_json._update(json_pool)
        assert pool_from_json.privileges is not None
        assert pool_from_json.privileges._exportApiAndStorageCredentialsInEnvironment is True

    def test_pool_retry_settings(self):
        pool = Pool(self.conn, "pool-name", "profile")

        json_pool = pool._to_json()
        assert json_pool['defaultRetrySettings'] is not None
        assert json_pool['defaultRetrySettings']['maxTotalRetries'] is None
        assert json_pool['defaultRetrySettings']['maxPerInstanceRetries'] is None

        pool.default_retry_settings = RetrySettings(36, 12)
        json_pool = pool._to_json()
        assert json_pool['defaultRetrySettings'] is not None
        assert json_pool['defaultRetrySettings']['maxTotalRetries'] is 36
        assert json_pool['defaultRetrySettings']['maxPerInstanceRetries'] is 12

        # fields that need to be non null for the deserialization to not fail
        json_pool['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_pool['uuid'] = str(uuid.uuid4())
        json_pool['state'] = 'Submitted'
        json_pool['runningCoreCount'] = 0
        json_pool['runningInstanceCount'] = 0

        pool_from_json = Pool(self.conn, "pool-name", "profile")
        pool_from_json._update(json_pool)
        assert pool_from_json.default_retry_settings is not None
        assert pool_from_json.default_retry_settings._maxTotalRetries is 36
        assert pool_from_json.default_retry_settings._maxPerInstanceRetries is 12

    def test_pool_flex_scheduling_serialization(self):
        pool = Pool(self.conn, "pool-with-flex-scheduling", "profile", scheduling_type=FlexScheduling())
        assert pool.scheduling_type is not None
        print(pool.scheduling_type)
        assert isinstance(pool.scheduling_type, FlexScheduling)
        assert pool.scheduling_type.schedulingType == "Flex"

        json_pool = pool._to_json()
        assert json_pool['schedulingType'] is not None
        assert json_pool['schedulingType'] == FlexScheduling.schedulingType

        # fields that need to be non null for the deserialization to not fail
        json_pool['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_pool['uuid'] = str(uuid.uuid4())
        json_pool['state'] = 'Submitted'
        json_pool['runningCoreCount'] = 0
        json_pool['runningInstanceCount'] = 0

        pool_from_json = Pool(self.conn, "pool-with-flex-scheduling-from-json", "profile")
        pool_from_json._update(json_pool)
        assert pool_from_json.scheduling_type is not None
        assert isinstance(pool_from_json.scheduling_type, FlexScheduling)
        assert pool_from_json.scheduling_type.schedulingType == FlexScheduling.schedulingType

    def test_pool_onDemand_scheduling_serialization(self):
        pool = Pool(self.conn, "pool-with-on-demand-scheduling", "profile", scheduling_type=OnDemandScheduling())
        assert pool.scheduling_type is not None
        print(pool.scheduling_type)
        assert isinstance(pool.scheduling_type, OnDemandScheduling)
        assert pool.scheduling_type.schedulingType == "OnDemand"

        json_pool = pool._to_json()
        assert json_pool['schedulingType'] is not None
        assert json_pool['schedulingType'] == OnDemandScheduling.schedulingType

        # fields that need to be non null for the deserialization to not fail
        json_pool['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_pool['uuid'] = str(uuid.uuid4())
        json_pool['state'] = 'Submitted'
        json_pool['runningCoreCount'] = 0
        json_pool['runningInstanceCount'] = 0

        pool_from_json = Pool(self.conn, "pool-with-on-demand-scheduling-from-json", "profile")
        pool_from_json._update(json_pool)
        assert pool_from_json.scheduling_type is not None
        assert isinstance(pool_from_json.scheduling_type, OnDemandScheduling)
        assert pool_from_json.scheduling_type.schedulingType == OnDemandScheduling.schedulingType

    def test_pool_reserved_scheduling_serialization(self):
        pool = Pool(self.conn, "pool-with-reserved-scheduling", "profile", scheduling_type=ReservedScheduling())
        pool.targeted_reserved_machine_key = "reservedMachine"
        assert pool.scheduling_type is not None
        print(pool.scheduling_type)
        assert isinstance(pool.scheduling_type, ReservedScheduling)
        assert pool.scheduling_type.schedulingType == "Reserved"

        json_pool = pool._to_json()
        assert json_pool['schedulingType'] is not None
        assert json_pool['schedulingType'] == ReservedScheduling.schedulingType
        assert json_pool['targetedReservedMachineKey'] is not None
        assert json_pool['targetedReservedMachineKey'] == "reservedMachine"

        # fields that need to be non null for the deserialization to not fail
        json_pool['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_pool['uuid'] = str(uuid.uuid4())
        json_pool['state'] = 'Submitted'
        json_pool['runningCoreCount'] = 0
        json_pool['runningInstanceCount'] = 0

        pool_from_json = Pool(self.conn, "pool-with-reserved-scheduling-from-json", "profile")
        pool_from_json._update(json_pool)
        assert pool_from_json.scheduling_type is not None
        assert isinstance(pool_from_json.scheduling_type, ReservedScheduling)
        assert pool_from_json.scheduling_type.schedulingType == ReservedScheduling.schedulingType
        assert pool.targeted_reserved_machine_key == "reservedMachine"

    def test_pool_forced_network_rules_serialization(self):
        pool = Pool(self.conn, "pool-with-forced-network-rules", "profile")
        inbound_rule = ForcedNetworkRule(True, "tcp", "1234", "bound-to-be-alive", priority="1000", description="Inbound test")
        outbound_rule = ForcedNetworkRule(False, "tcp", public_port="666", public_host="bound-to-the-devil", priority="1000", description="Outbound test")
        rules = [
            inbound_rule,
            outbound_rule,
        ]
        pool.forced_network_rules = rules
        assert pool.forced_network_rules is not None
        assert len(pool.forced_network_rules) == 2

        json_pool = pool._to_json()
        assert json_pool['forcedNetworkRules'] is not None
        assert len(json_pool['forcedNetworkRules']) == 2
        json_inbound_rule = json_pool['forcedNetworkRules'][0]
        assert json_inbound_rule["inbound"] == inbound_rule.inbound
        assert json_inbound_rule["proto"] == inbound_rule.proto
        assert json_inbound_rule["port"] == inbound_rule.port
        assert json_inbound_rule["to"] == inbound_rule.to
        assert json_inbound_rule["priority"] == inbound_rule.priority
        assert json_inbound_rule["description"] == inbound_rule.description
        json_outbound_rule = json_pool['forcedNetworkRules'][1]
        assert json_outbound_rule["inbound"] == outbound_rule.inbound
        assert json_outbound_rule["proto"] == outbound_rule.proto
        assert json_outbound_rule["priority"] == outbound_rule.priority
        assert json_outbound_rule["description"] == outbound_rule.description

        # fields that need to be non null for the deserialization to not fail
        json_pool['creationDate'] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        json_pool['uuid'] = str(uuid.uuid4())
        json_pool['state'] = 'Submitted'
        json_pool['runningCoreCount'] = 0
        json_pool['runningInstanceCount'] = 0

        pool_from_json = Pool(self.conn, "pool-with-forced-network-rules-from-json", "profile")
        pool_from_json._update(json_pool)
        assert pool_from_json.forced_network_rules is not None
        assert len(pool_from_json.forced_network_rules) == 2
        inbound_from_json = pool_from_json.forced_network_rules[0]
        assert inbound_from_json.inbound == inbound_rule.inbound
        assert inbound_from_json.proto == inbound_rule.proto
        assert inbound_from_json.port == inbound_rule.port
        assert inbound_from_json.to == inbound_rule.to
        assert inbound_from_json.priority == inbound_rule.priority
        assert inbound_from_json.description == inbound_rule.description
        outbound_from_json = pool_from_json.forced_network_rules[1]
        assert outbound_from_json.inbound == outbound_rule.inbound
        assert outbound_from_json.proto == outbound_rule.proto
        assert outbound_from_json.priority == outbound_rule.priority
        assert outbound_from_json.description == outbound_rule.description
