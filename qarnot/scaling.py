"""Module to handle scaling policies"""

# Copyright 2017 Qarnot computing
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, List, Optional, Union
from datetime import datetime, time
from enum import Enum
import abc


class DayOfWeek(str, Enum):
    """Days of the week accepted by weekly recurring scaling periods."""
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        # Display only the value (e.g. 'monday') instead of the verbose
        # default "<DayOfWeek.MONDAY: 'monday'>", including inside lists.
        return repr(self.value)


def _parse_day(value: Union['DayOfWeek', str]) -> 'DayOfWeek':
    """Normalize a day value into a :class:`DayOfWeek` (case-insensitive).

    :param value: a :class:`DayOfWeek` or a day name string (e.g. "Monday")
    :returns: the matching :class:`DayOfWeek`
    :raises ValueError: if the value is not a valid day of the week
    """
    if isinstance(value, DayOfWeek):
        return value
    return DayOfWeek(str(value).lower())


def _parse_time_utc(value: Any) -> Optional[time]:
    """Parse an API time-of-day string ("HH:MM:SS[.ffffff]") into a time.

    :param value: a time-of-day string, a :class:`datetime.time`, or None
    :returns: the parsed :class:`datetime.time`, or None
    """
    if value is None or isinstance(value, time):
        return value
    text = str(value)
    if "." in text:
        base, frac = text.split(".", 1)
        frac = (frac + "000000")[:6]  # pad/truncate to microseconds
        return datetime.strptime("{}.{}".format(base, frac), "%H:%M:%S.%f").time()
    return datetime.strptime(text, "%H:%M:%S").time()


class TimePeriodSpecification():
    """Represents a time period specification for scaling policies."""
    _type: str = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'TimePeriodSpecification':
        """Create a time period specification from json.

        :param dict json: Dictionary representing the time period
        :returns: The created :class:`~qarnot.scaling.TimePeriodSpecification`.
        """
        if json is None:
            return None

        period_type: str = json.get("type")
        if period_type == TimePeriodAlways._type:
            name: Optional[str] = json.get("name")
            return TimePeriodAlways(name=name)
        elif period_type == TimePeriodWeeklyRecurring._type:
            name = json.get("name")
            days: List[Union[DayOfWeek, str]] = [_parse_day(d) for d in json.get("days", [])]
            start_time_utc: Optional[time] = _parse_time_utc(json.get("startTimeUtc"))
            end_time_utc: Optional[time] = _parse_time_utc(json.get("endTimeUtc"))
            return TimePeriodWeeklyRecurring(days=days, start_time_utc=start_time_utc,
                                             end_time_utc=end_time_utc, name=name)
        else:
            return None

    @abc.abstractmethod
    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :raises NotImplementedError: this is an abstract method, it should be overridden in child classes
        """

    def __str__(self) -> str:
        return "time period {}.".format(self._type)

    def __repr__(self) -> str:
        return str(self._type)


class TimePeriodAlways(TimePeriodSpecification):
    """Represents a time period that is always active."""
    _type: str = "Always"

    def __init__(self, name: str = None):
        """Create a new time period that is always active.

        :param str name: optional name for the time period
        """
        self.name: Optional[str] = name

    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :return: the json elements of the class.
        :rtype: `dict`
        """
        result = {
            "type": self._type
        }
        if self.name is not None:
            result["name"] = self.name
        return result

    def __str__(self) -> str:
        if self.name:
            return "Time period '{}' (Always).".format(self.name)
        return "Time period Always."

    def __repr__(self) -> str:
        if self.name:
            return "{}: {}".format(self._type, self.name)
        return self._type


class TimePeriodWeeklyRecurring(TimePeriodSpecification):
    """Represents a weekly recurring time period."""
    _type: str = "Weekly"

    def __init__(self, days: List[Union[DayOfWeek, str]], start_time_utc: time, end_time_utc: time, name: str = None):
        """Create a new weekly recurring time period.

        :param days: list of days, as :class:`DayOfWeek` members or day-name
            strings (e.g. [DayOfWeek.MONDAY, "tuesday"]); strings are
            case-insensitive
        :param datetime.time start_time_utc: start time in UTC (e.g., time(9, 0, 0))
        :param datetime.time end_time_utc: end time in UTC (e.g., time(17, 0, 0))
        :param str name: optional name for the time period
        :raises ValueError: if a day value is not a valid day of the week
        """
        self.name: Optional[str] = name
        self.days: List[DayOfWeek] = [_parse_day(d) for d in days]
        self.start_time_utc: time = start_time_utc
        self.end_time_utc: time = end_time_utc

    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :return: the json elements of the class.
        :rtype: `dict`
        """
        result = {
            "type": self._type,
            "days": [d.value for d in self.days],
            "startTimeUtc": self.start_time_utc.isoformat(),
            "endTimeUtc": self.end_time_utc.isoformat()
        }
        if self.name is not None:
            result["name"] = self.name
        return result

    def __str__(self) -> str:
        name_str = "'{}'".format(self.name) if self.name else "Weekly"
        return "Time period {} on {} from {} to {}.".format(
            name_str, self.days, self.start_time_utc, self.end_time_utc)

    def __repr__(self) -> str:
        return "{}: {} {}-{}".format(self._type, self.days, self.start_time_utc, self.end_time_utc)


class ScalingPolicy():
    """Represents a scaling policy."""
    _type: str = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'ScalingPolicy':
        """Create a scaling policy from json.

        :param dict json: Dictionary representing the scaling policy
        :returns: The created :class:`~qarnot.scaling.ScalingPolicy`.
        """
        if json is None:
            return None

        policy_type: str = json.get("type")
        name: Optional[str] = json.get("name")
        enabled_periods_json: List[Dict] = json.get("enabledPeriods", [])
        enabled_periods: List[TimePeriodSpecification] = []
        for p in enabled_periods_json:
            enabled_periods.append(TimePeriodSpecification.from_json(p))

        if policy_type == FixedScalingPolicy._type:
            slots_count: int = json.get("slotsCount")
            return FixedScalingPolicy(slots_count=slots_count, name=name, enabled_periods=enabled_periods)
        elif policy_type == ManagedTasksQueueScalingPolicy._type:
            min_total_slots: Optional[int] = json.get("minTotalSlots")
            max_total_slots: Optional[int] = json.get("maxTotalSlots")
            min_idle_slots: Optional[int] = json.get("minIdleSlots")
            min_idle_time_seconds: Optional[int] = json.get("minIdleTimeSeconds")
            scaling_factor: Optional[float] = json.get("scalingFactor")
            return ManagedTasksQueueScalingPolicy(
                min_total_slots=min_total_slots,
                max_total_slots=max_total_slots,
                min_idle_slots=min_idle_slots,
                min_idle_time_seconds=min_idle_time_seconds,
                scaling_factor=scaling_factor,
                name=name,
                enabled_periods=enabled_periods
            )
        else:
            return None

    @abc.abstractmethod
    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :raises NotImplementedError: this is an abstract method, it should be overridden in child classes
        """

    def __str__(self) -> str:
        return "scaling policy {}.".format(self._type)

    def __repr__(self) -> str:
        return str(self._type)


class FixedScalingPolicy(ScalingPolicy):
    """Represents a fixed scaling policy with a constant number of slots."""
    _type: str = "Fixed"

    def __init__(self, slots_count: int, name: str = None,
                 enabled_periods: List[TimePeriodSpecification] = None):
        """Create a new fixed scaling policy.

        :param int slots_count: the number of slots to allocate
        :param str name: optional name for the policy
        :param List[TimePeriodSpecification] enabled_periods: optional list of time periods when this policy is enabled
        """
        self.slots_count: int = slots_count
        self.name: Optional[str] = name
        self.enabled_periods: List[TimePeriodSpecification] = enabled_periods or []

    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :return: the json elements of the class.
        :rtype: `dict`
        """
        result = {
            "type": self._type,
            "slotsCount": self.slots_count
        }
        if self.name is not None:
            result["name"] = self.name
        if self.enabled_periods:
            enabled_periods = []
            for p in self.enabled_periods:
                enabled_periods.append(p.to_json())
            result["enabledPeriods"] = enabled_periods
        return result

    def __str__(self) -> str:
        name_str = "'{}'".format(self.name) if self.name else "Fixed"
        return "Scaling policy {} with {} slots.".format(name_str, self.slots_count)

    def __repr__(self) -> str:
        return "{}: {} slots".format(self._type, self.slots_count)


class ManagedTasksQueueScalingPolicy(ScalingPolicy):
    """Represents a managed tasks queue scaling policy that scales based on task queue."""
    _type: str = "ManagedTasksQueue"

    def __init__(self, min_total_slots: int = None, max_total_slots: int = None,
                 min_idle_slots: int = None, min_idle_time_seconds: int = None,
                 scaling_factor: float = None, name: str = None,
                 enabled_periods: List[TimePeriodSpecification] = None):
        """Create a new managed tasks queue scaling policy.

        :param int min_total_slots: minimum total slots to maintain
        :param int max_total_slots: maximum total slots allowed
        :param int min_idle_slots: minimum number of idle slots to maintain
        :param int min_idle_time_seconds: minimum time in seconds before scaling down idle slots
        :param float scaling_factor: factor for scaling calculations
        :param str name: optional name for the policy
        :param List[TimePeriodSpecification] enabled_periods: optional list of time periods when this policy is enabled
        """
        self.min_total_slots: Optional[int] = min_total_slots
        self.max_total_slots: Optional[int] = max_total_slots
        self.min_idle_slots: Optional[int] = min_idle_slots
        self.min_idle_time_seconds: Optional[int] = min_idle_time_seconds
        self.scaling_factor: Optional[float] = scaling_factor
        self.name: Optional[str] = name
        self.enabled_periods: List[TimePeriodSpecification] = enabled_periods or []

    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :return: the json elements of the class.
        :rtype: `dict`
        """
        result: Dict[str, Any] = {
            "type": self._type
        }
        if self.name is not None:
            result["name"] = self.name
        if self.min_total_slots is not None:
            result["minTotalSlots"] = self.min_total_slots
        if self.max_total_slots is not None:
            result["maxTotalSlots"] = self.max_total_slots
        if self.min_idle_slots is not None:
            result["minIdleSlots"] = self.min_idle_slots
        if self.min_idle_time_seconds is not None:
            result["minIdleTimeSeconds"] = self.min_idle_time_seconds
        if self.scaling_factor is not None:
            result["scalingFactor"] = self.scaling_factor
        if self.enabled_periods:
            enabled_periods = []
            for p in self.enabled_periods:
                enabled_periods.append(p.to_json())
            result["enabledPeriods"] = enabled_periods
        return result

    def __str__(self) -> str:
        name_str = "'{}'".format(self.name) if self.name else "ManagedTasksQueue"
        return "Scaling policy {} (min={}, max={}, idle={}).".format(
            name_str, self.min_total_slots, self.max_total_slots, self.min_idle_slots)

    def __repr__(self) -> str:
        return "{}: min={}, max={}".format(self._type, self.min_total_slots, self.max_total_slots)


class Scaling():
    """Container for scaling policies."""

    def __init__(self, policies: List[ScalingPolicy] = None):
        """Create a new scaling configuration.

        :param List[ScalingPolicy] policies: list of scaling policies
        """
        self.policies: List[ScalingPolicy] = policies or []
        self.active_policy_name: Optional[str] = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> 'Scaling':
        """Create a scaling configuration from json.

        :param dict json: Dictionary representing the scaling configuration
        :returns: The created :class:`~qarnot.scaling.Scaling`.
        """
        if json is None:
            return None

        policies_json: List[Dict] = json.get("policies", [])
        policies: List[ScalingPolicy] = []

        for p in policies_json:
            policies.append(ScalingPolicy.from_json(p))

        scaling = Scaling(policies=policies)
        scaling.active_policy_name = json.get("activePolicyName")
        return scaling

    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :return: the json elements of the class.
        :rtype: `dict`
        """
        result = {}
        if self.policies:
            policies = []
            for p in self.policies:
                policies.append(p.to_json())
            result["policies"] = policies
        return result

    def __str__(self) -> str:
        return "Scaling with {} policies (active: {}).".format(len(self.policies), self.active_policy_name)

    def __repr__(self) -> str:
        return "Scaling: {} policies".format(len(self.policies))
