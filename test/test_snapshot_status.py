import pytest

from qarnot.snapshot import Snapshot, TriggeredStatus, InProgressStatus, SuccessStatus, FailedStatus

from .mock_snapshot_status import default_json_status

class TestStatusProperties:
    @pytest.mark.parametrize("property_name, expected_value", [
        ("_id", default_json_status["id"]),
        ("_task_uuid", default_json_status["taskUuid"]),
        ("_trigger_date", default_json_status["triggerDate"]),
        ("_last_update_date", default_json_status["lastUpdateDate"]),
        ("_size_to_upload", default_json_status["sizeToUpload"]),
        ("_transferred_size", default_json_status["transferredSize"]),
    ])
    def test_create_snapshot_status_from_json_hydrate_property_values(self, property_name,  expected_value):
        snapshot_from_json = Snapshot.from_json(default_json_status)
        assert getattr(snapshot_from_json, property_name) == expected_value

    @pytest.mark.parametrize("property_names, expected_value", [
        (["_snapshot_config", "_whitelist"], default_json_status["snapshotConfig"]["whitelist"]),
        (["_snapshot_config", "_blacklist"], default_json_status["snapshotConfig"]["blacklist"]),
        (["_snapshot_config", "_bucket_name"], default_json_status["snapshotConfig"]["bucket"]),
        (["_snapshot_config", "_bucket_prefix"], default_json_status["snapshotConfig"]["bucketPrefix"]),
    ])
    def test_create_snapshot_status_from_json_hydrate_configuration_subproperty_values(self, property_names,  expected_value):
        snapshot_from_json = Snapshot.from_json(default_json_status)
        value = getattr(snapshot_from_json, property_names[0])
        for property_name in property_names[1:]:
            if type(property_name) is int:
                value = value[property_name]
            else:
                value = getattr(value, property_name)
        assert value == expected_value
    
    @pytest.mark.parametrize("json_value, expected_status_type", [
        ("triggered", TriggeredStatus),
        ("Triggered", TriggeredStatus),
        ("inProgress", InProgressStatus),
        ("InProgress", InProgressStatus),
        ("success", SuccessStatus),
        ("failure", FailedStatus)])
    def test_snapshot_status_correctly_deserialized(self, json_value, expected_status_type: type):
        json = { "status": json_value }
        snapshot_from_json = Snapshot.from_json(json)
        assert snapshot_from_json._status is not None
        assert type(snapshot_from_json._status) == expected_status_type

    def test_snapshot_status_with_null_values_does_not_throw_at_deserialization(self):
        json = {
            "id": None,
            "taskUuid": None,
            "triggerDate": None,
            "lastUpdateDate": None,
            "snapshotConfig": None,
            "status": None,
            "sizeToUpload": None,
            "transferredSize": None,
        }
        snapshot_from_json = Snapshot.from_json(json)
        assert snapshot_from_json._status is not None
        assert type(snapshot_from_json._status) == TriggeredStatus

        json = {
            "snapshotConfig":
            {
                "whitelist": None,
                "blacklist": None,
                "bucket": None,
                "bucketPrefix": None
            }
        }
        snapshot_from_json = Snapshot.from_json(json)
        assert snapshot_from_json._snapshot_config is not None
