import pytest
from datetime import time
from qarnot.scaling import (TimePeriodSpecification, TimePeriodAlways, TimePeriodWeeklyRecurring,
    ScalingPolicy, FixedScalingPolicy, ManagedTasksQueueScalingPolicy, Scaling, DayOfWeek)


class TestTimePeriod:
    # Deserialization tests

    def test_TimePeriodAlways_deserialization(self):
        json = {
            "type": "Always",
            "name": "always-period"
        }
        period = TimePeriodSpecification.from_json(json)
        assert period is not None
        assert isinstance(period, TimePeriodAlways)
        assert period.name == "always-period"

    def test_TimePeriodAlways_deserialization_without_name(self):
        json = {
            "type": "Always"
        }
        period = TimePeriodSpecification.from_json(json)
        assert period is not None
        assert isinstance(period, TimePeriodAlways)
        assert period.name is None

    def test_TimePeriodWeeklyRecurring_deserialization(self):
        json = {
            "type": "Weekly",
            "name": "weekday-hours",
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "startTimeUtc": "09:00:00",
            "endTimeUtc": "17:00:00"
        }
        period = TimePeriodSpecification.from_json(json)
        assert period is not None
        assert isinstance(period, TimePeriodWeeklyRecurring)
        assert period.name == "weekday-hours"
        assert period.days == [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
                               DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]
        assert period.start_time_utc == time(9, 0, 0)
        assert period.end_time_utc == time(17, 0, 0)

    def test_TimePeriodWeeklyRecurring_deserialization_fractional_seconds(self):
        json = {
            "type": "Weekly",
            "days": ["Saturday"],
            "startTimeUtc": "00:00:00",
            "endTimeUtc": "23:59:59.9999999"
        }
        period = TimePeriodSpecification.from_json(json)
        assert isinstance(period, TimePeriodWeeklyRecurring)
        assert period.start_time_utc == time(0, 0, 0)
        assert period.end_time_utc == time(23, 59, 59, 999999)

    def test_TimePeriodWeeklyRecurring_accepts_string_days(self):
        period = TimePeriodWeeklyRecurring(
            days=["Monday", DayOfWeek.FRIDAY, "SUNDAY"],
            start_time_utc=time(9, 0, 0),
            end_time_utc=time(17, 0, 0)
        )
        assert period.days == [DayOfWeek.MONDAY, DayOfWeek.FRIDAY, DayOfWeek.SUNDAY]

    def test_TimePeriodWeeklyRecurring_invalid_day_raises(self):
        with pytest.raises(ValueError):
            TimePeriodWeeklyRecurring(
                days=["Mondai"],
                start_time_utc=time(9, 0, 0),
                end_time_utc=time(17, 0, 0)
            )

    def test_TimePeriodWeeklyRecurring_deserialization_invalid_day_raises(self):
        json = {
            "type": "Weekly",
            "days": ["Mondai"],
            "startTimeUtc": "09:00:00",
            "endTimeUtc": "17:00:00"
        }
        with pytest.raises(ValueError):
            TimePeriodSpecification.from_json(json)

    def test_TimePeriod_unknown_type_returns_none(self):
        json = {
            "type": "UnknownType"
        }
        period = TimePeriodSpecification.from_json(json)
        assert period is None

    def test_TimePeriod_none_returns_none(self):
        period = TimePeriodSpecification.from_json(None)
        assert period is None

    # Serialization tests

    def test_TimePeriodAlways_serialization(self):
        period = TimePeriodAlways(name="always-period")
        json_dict = period.to_json()
        assert json_dict["type"] == "Always"
        assert json_dict["name"] == "always-period"

    def test_TimePeriodAlways_serialization_without_name(self):
        period = TimePeriodAlways()
        json_dict = period.to_json()
        assert json_dict["type"] == "Always"
        assert "name" not in json_dict

    def test_TimePeriodWeeklyRecurring_serialization(self):
        period = TimePeriodWeeklyRecurring(
            days=[DayOfWeek.MONDAY, DayOfWeek.FRIDAY],
            start_time_utc=time(8, 0, 0),
            end_time_utc=time(18, 0, 0),
            name="work-days"
        )
        json_dict = period.to_json()
        assert json_dict["type"] == "Weekly"
        assert json_dict["name"] == "work-days"
        assert json_dict["days"] == ["monday", "friday"]
        assert json_dict["startTimeUtc"] == "08:00:00"
        assert json_dict["endTimeUtc"] == "18:00:00"

    def test_TimePeriodWeeklyRecurring_serialization_without_name(self):
        period = TimePeriodWeeklyRecurring(
            days=[DayOfWeek.SATURDAY, DayOfWeek.SUNDAY],
            start_time_utc=time(0, 0, 0),
            end_time_utc=time(23, 59, 59)
        )
        json_dict = period.to_json()
        assert json_dict["type"] == "Weekly"
        assert "name" not in json_dict
        assert json_dict["days"] == ["saturday", "sunday"]


class TestScalingPolicy:
    # Deserialization tests

    def test_FixedScalingPolicy_deserialization(self):
        json = {
            "type": "Fixed",
            "name": "fixed-policy",
            "slotsCount": 10,
            "enabledPeriods": [
                {"type": "Always", "name": "always"}
            ]
        }
        policy = ScalingPolicy.from_json(json)
        assert policy is not None
        assert isinstance(policy, FixedScalingPolicy)
        assert policy.name == "fixed-policy"
        assert policy.slots_count == 10
        assert len(policy.enabled_periods) == 1
        assert isinstance(policy.enabled_periods[0], TimePeriodAlways)

    def test_FixedScalingPolicy_deserialization_minimal(self):
        json = {
            "type": "Fixed",
            "slotsCount": 5
        }
        policy = ScalingPolicy.from_json(json)
        assert policy is not None
        assert isinstance(policy, FixedScalingPolicy)
        assert policy.name is None
        assert policy.slots_count == 5
        assert len(policy.enabled_periods) == 0

    def test_ManagedTasksQueueScalingPolicy_deserialization(self):
        json = {
            "type": "ManagedTasksQueue",
            "name": "autoscale-policy",
            "minTotalSlots": 2,
            "maxTotalSlots": 20,
            "minIdleSlots": 1,
            "minIdleTimeSeconds": 300,
            "scalingFactor": 1.5,
            "enabledPeriods": [
                {
                    "type": "Weekly",
                    "days": ["Monday", "Friday"],
                    "startTimeUtc": "08:00:00",
                    "endTimeUtc": "18:00:00"
                }
            ]
        }
        policy = ScalingPolicy.from_json(json)
        assert policy is not None
        assert isinstance(policy, ManagedTasksQueueScalingPolicy)
        assert policy.name == "autoscale-policy"
        assert policy.min_total_slots == 2
        assert policy.max_total_slots == 20
        assert policy.min_idle_slots == 1
        assert policy.min_idle_time_seconds == 300
        assert policy.scaling_factor == 1.5
        assert len(policy.enabled_periods) == 1
        assert isinstance(policy.enabled_periods[0], TimePeriodWeeklyRecurring)

    def test_ManagedTasksQueueScalingPolicy_deserialization_minimal(self):
        json = {
            "type": "ManagedTasksQueue"
        }
        policy = ScalingPolicy.from_json(json)
        assert policy is not None
        assert isinstance(policy, ManagedTasksQueueScalingPolicy)
        assert policy.name is None
        assert policy.min_total_slots is None
        assert policy.max_total_slots is None
        assert policy.min_idle_slots is None
        assert policy.min_idle_time_seconds is None
        assert policy.scaling_factor is None

    def test_ScalingPolicy_unknown_type_returns_none(self):
        json = {
            "type": "UnknownPolicy"
        }
        policy = ScalingPolicy.from_json(json)
        assert policy is None

    def test_ScalingPolicy_none_returns_none(self):
        policy = ScalingPolicy.from_json(None)
        assert policy is None

    # Serialization tests

    def test_FixedScalingPolicy_serialization(self):
        policy = FixedScalingPolicy(
            slots_count=10,
            name="fixed-policy",
            enabled_periods=[TimePeriodAlways(name="always")]
        )
        json_dict = policy.to_json()
        assert json_dict["type"] == "Fixed"
        assert json_dict["name"] == "fixed-policy"
        assert json_dict["slotsCount"] == 10
        assert len(json_dict["enabledPeriods"]) == 1
        assert json_dict["enabledPeriods"][0]["type"] == "Always"

    def test_FixedScalingPolicy_serialization_minimal(self):
        policy = FixedScalingPolicy(slots_count=5)
        json_dict = policy.to_json()
        assert json_dict["type"] == "Fixed"
        assert json_dict["slotsCount"] == 5
        assert "name" not in json_dict
        assert "enabledPeriods" not in json_dict

    def test_ManagedTasksQueueScalingPolicy_serialization(self):
        policy = ManagedTasksQueueScalingPolicy(
            min_total_slots=2,
            max_total_slots=20,
            min_idle_slots=1,
            min_idle_time_seconds=300,
            scaling_factor=1.5,
            name="autoscale",
            enabled_periods=[
                TimePeriodWeeklyRecurring(
                    days=[DayOfWeek.MONDAY, DayOfWeek.TUESDAY],
                    start_time_utc=time(9, 0, 0),
                    end_time_utc=time(17, 0, 0)
                )
            ]
        )
        json_dict = policy.to_json()
        assert json_dict["type"] == "ManagedTasksQueue"
        assert json_dict["name"] == "autoscale"
        assert json_dict["minTotalSlots"] == 2
        assert json_dict["maxTotalSlots"] == 20
        assert json_dict["minIdleSlots"] == 1
        assert json_dict["minIdleTimeSeconds"] == 300
        assert json_dict["scalingFactor"] == 1.5
        assert len(json_dict["enabledPeriods"]) == 1

    def test_ManagedTasksQueueScalingPolicy_serialization_minimal(self):
        policy = ManagedTasksQueueScalingPolicy()
        json_dict = policy.to_json()
        assert json_dict["type"] == "ManagedTasksQueue"
        assert "name" not in json_dict
        assert "minTotalSlots" not in json_dict
        assert "maxTotalSlots" not in json_dict
        assert "minIdleSlots" not in json_dict
        assert "minIdleTimeSeconds" not in json_dict
        assert "scalingFactor" not in json_dict
        assert "enabledPeriods" not in json_dict


class TestScaling:
    # Deserialization tests

    def test_Scaling_deserialization(self):
        json = {
            "policies": [
                {
                    "type": "Fixed",
                    "name": "default",
                    "slotsCount": 5
                },
                {
                    "type": "ManagedTasksQueue",
                    "name": "autoscale",
                    "minTotalSlots": 1,
                    "maxTotalSlots": 10
                }
            ],
            "activePolicyName": "default"
        }
        scaling = Scaling.from_json(json)
        assert scaling is not None
        assert len(scaling.policies) == 2
        assert isinstance(scaling.policies[0], FixedScalingPolicy)
        assert isinstance(scaling.policies[1], ManagedTasksQueueScalingPolicy)
        assert scaling.active_policy_name == "default"

    def test_Scaling_deserialization_empty(self):
        json = {}
        scaling = Scaling.from_json(json)
        assert scaling is not None
        assert len(scaling.policies) == 0
        assert scaling.active_policy_name is None

    def test_Scaling_deserialization_none(self):
        scaling = Scaling.from_json(None)
        assert scaling is None

    # Serialization tests

    def test_Scaling_serialization(self):
        scaling = Scaling(policies=[
            FixedScalingPolicy(slots_count=8, name="fixed"),
            ManagedTasksQueueScalingPolicy(
                min_total_slots=2,
                max_total_slots=16,
                name="managed"
            )
        ])
        json_dict = scaling.to_json()
        assert len(json_dict["policies"]) == 2
        assert json_dict["policies"][0]["type"] == "Fixed"
        assert json_dict["policies"][0]["slotsCount"] == 8
        assert json_dict["policies"][1]["type"] == "ManagedTasksQueue"
        assert json_dict["policies"][1]["minTotalSlots"] == 2

    def test_Scaling_serialization_empty(self):
        scaling = Scaling()
        json_dict = scaling.to_json()
        assert "policies" not in json_dict

    def test_Scaling_serialization_does_not_include_active_policy_name(self):
        scaling = Scaling(policies=[FixedScalingPolicy(slots_count=5)])
        json_dict = scaling.to_json()
        assert "activePolicyName" not in json_dict
