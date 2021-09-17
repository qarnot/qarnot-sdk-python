import datetime
import pytest

from qarnot.status import Status

from .mock_status import default_json_status

class TestStatusProperties:
    @pytest.mark.parametrize("property_name, expected_value", [
        ("last_update_timestamp", default_json_status["lastUpdateTimestamp"]),
    ])
    def test_create_status_hydrate_property_values(self, property_name,  expected_value):
        status = Status(default_json_status)
        assert getattr(status, property_name) == expected_value

    @pytest.mark.parametrize("property_names, expected_value", [
        (["running_instances_info", "snapshot_results"], default_json_status["runningInstancesInfo"]["snapshotResults"]),
        (["running_instances_info", "running_core_count_by_cpu_model"], default_json_status["runningInstancesInfo"]["runningCoreCountByCpuModel"]),
        (["execution_time_by_cpu_model", 0, "model"], default_json_status["executionTimeByCpuModel"][0]["model"]),
        (["execution_time_by_cpu_model", 0, "time"], default_json_status["executionTimeByCpuModel"][0]["time"]),
        (["execution_time_by_cpu_model", 0, "core"], default_json_status["executionTimeByCpuModel"][0]["core"]),
    ])
    def test_create_status_hydrate_subproperty_values(self, property_names,  expected_value):
        status = Status(default_json_status)
        value = getattr(status, property_names[0])
        for property_name in property_names[1:]:
            if type(property_name) is int:
                value = value[property_name]
            else:
                value = getattr(value, property_name)
        assert value == expected_value
