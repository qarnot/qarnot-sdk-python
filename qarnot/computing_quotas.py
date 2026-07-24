# Copyright 2025 Qarnot computing
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

from typing import Optional, List, Sequence, Dict, Any


def _indented_reservation_lines(reserved: Optional[Sequence[object]]) -> str:
    """Format each reservation's ``str()`` on its own line, indented by 4 spaces.

    :param reserved: the reservations to format, if any.
    :returns: an empty string if there is no reservation, otherwise one indented line per reservation, prefixed by a newline.
    """
    return "".join("\n    {}".format(r) for r in (reserved or []))


class UserSchedulingQuota(object):
    """Describes a scheduling quota for the user.
    """

    def __init__(self, max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
        """Create a new UserSchedulingQuota object describing a scheduling quota for the user.

        :param int max_cores: Maximum number of cores that can be simultaneously used with this scheduling plan.
        :param int running_cores_count: Number of cores that are currently running with this scheduling plan.
        :param int max_instances: Maximum number of instances that can be simultaneously used with this scheduling plan.
        :param int running_instances_count: Number of instances that are currently running with this scheduling plan.
        :returns: The created :class:`~qarnot.computing_quotas.UserSchedulingQuota`.
        """
        self.max_cores = max_cores
        """:type: :class:`int`

        Maximum number of cores that can be simultaneously used with this scheduling plan.
        """
        self.running_cores_count = running_cores_count
        """:type: :class:`int`

        Number of cores that are currently running with this scheduling plan.
        """
        self.max_instances = max_instances
        """:type: :class:`int`

        Maximum number of instances that can be simultaneously used with this scheduling plan.
        """
        self.running_instances_count = running_instances_count
        """:type: :class:`int`

        Number of instances that are currently running with this scheduling plan.
        """

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new UserSchedulingQuota object from json describing a scheduling quota for a user.

        :param dict json: Dictionary representing the user scheduling plan
        :returns: The created :class:`~qarnot.computing_quotas.UserSchedulingQuota`.
        """
        if json is None:
            return None
        return cls(
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )

    def __str__(self) -> str:
        return "{}/{} instances, {}/{} cores.".format(
            self.running_instances_count, self.max_instances, self.running_cores_count, self.max_cores)

    def __repr__(self) -> str:
        return "computing_quotas.UserSchedulingQuota(max_instances: {}, running_instances_count: {}, max_cores: {}, running_cores_count: {})".format(
            self.max_instances, self.running_instances_count, self.max_cores, self.running_cores_count)


class UserReservedSchedulingQuota(UserSchedulingQuota):
    """Describes a reserved scheduling quota for the user.
    """

    def __init__(self, reservation_name: str, machine_key: str, max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
        """Create a new UserReservedSchedulingQuota object describing a reserved scheduling quota for the user.

        :param str machine_key: Machine key of the reservation.
        :param int max_cores: Maximum number of cores that can be simultaneously used with this reserved machine specification.
        :param int running_cores_count: Number of cores that are currently running with this reserved machine specification.
        :param int max_instances: Maximum number of instances that can be simultaneously used with this reserved machine specification.
        :param int running_instances_count: Number of instances that are currently running with this reserved machine specification.
        :returns: The created :class:`~qarnot.computing_quotas.UserReservedSchedulingQuota`.
        """
        super().__init__(max_cores, running_cores_count, max_instances, running_instances_count)
        self.machine_key = machine_key
        """:type: :class:`str`

        Machine key of the reservation.
        """
        self.reservation_name = reservation_name
        """:type: :class:`str`

        Name of the reservation.
        """

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new UserReservedSchedulingQuota object from json describing a reserved scheduling quota for a user.

        :param dict json: Dictionary representing the user reserved scheduling quota
        :returns: The created :class:`~qarnot.computing_quotas.UserReservedSchedulingQuota`.
        """
        if json is None:
            return None
        return cls(
            json.get('reservationName'),
            json.get('machineKey'),
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )

    def __str__(self) -> str:
        return "reservation '{}': {}/{} instances, {}/{} cores.".format(
            self.reservation_name, self.running_instances_count, self.max_instances, self.running_cores_count, self.max_cores)

    def __repr__(self) -> str:
        return "computing_quotas.UserReservedSchedulingQuota(reservation_name: {}, machine_key: {}, max_instances: {}, " \
            "running_instances_count: {}, max_cores: {}, running_cores_count: {})".format(
                self.reservation_name, self.machine_key, self.max_instances, self.running_instances_count, self.max_cores, self.running_cores_count)


class UserComputingQuotas(object):
    """Describes the user's computing quotas.
    """

    def __init__(self, flex: UserSchedulingQuota, on_demand: UserSchedulingQuota, reserved: List[UserReservedSchedulingQuota]):
        """Create a new UserComputingQuotas object describing the user's computing quotas.

        :param `~qarnot.computing_quotas.UserSchedulingQuota` flex: Quotas for Flex scheduling plan.
        :param `~qarnot.computing_quotas.UserSchedulingQuota` on_demand: Quotas for OnDemand scheduling plan.
        :param List of `~qarnot.computing_quotas.UserReservedSchedulingQuota` reserved: Quotas for Reserved scheduling plan.
        :returns: The created :class:`~qarnot.computing_quotas.UserComputingQuotas`.
        """
        self.flex = flex
        """:type: :class:`~qarnot.computing_quotas.UserSchedulingQuota`

        Quotas for Flex scheduling plan."""
        self.on_demand = on_demand
        """:type: :class:`~qarnot.computing_quotas.UserSchedulingQuota`

        Quotas for OnDemand scheduling plan."""
        self.reserved = reserved
        """:type: list(:class:`~qarnot.computing_quotas.UserReservedSchedulingQuota`)

        Quotas for Reserved scheduling plan."""

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new UserComputingQuotas object from json describing the user's computing quotas.

        :param dict json: Dictionary representing the user computing quota
        :returns: The created :class:`~qarnot.computing_quotas.UserComputingQuotas`.
        """
        if json is None:
            return None
        return cls(
            UserSchedulingQuota.from_json(json.get('flex')),
            UserSchedulingQuota.from_json(json.get('onDemand')),
            [UserReservedSchedulingQuota.from_json(v) for v in (json.get('reserved') if json.get('reserved') is not None else []) if v is not None]
        )

    def __str__(self) -> str:
        return "flex: {}, on_demand: {}, {} reserved quota(s).".format(
            self.flex, self.on_demand, len(self.reserved) if self.reserved is not None else 0
        ) + _indented_reservation_lines(self.reserved)

    def __repr__(self) -> str:
        return "computing_quotas.UserComputingQuotas(flex: {!r}, on_demand: {!r}, reserved: {!r})".format(
            self.flex, self.on_demand, self.reserved)


class OrganizationSchedulingQuota(object):
    """Describes a scheduling quota for the organization.
    """

    def __init__(self, max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
        """Create a new OrganizationSchedulingQuota object describing a scheduling quota for the organization.

        :param int max_cores: Maximum number of cores that can be simultaneously used with this scheduling plan.
        :param int running_cores_count: Number of cores that are currently running with this scheduling plan.
        :param int max_instances: Maximum number of instances that can be simultaneously used with this scheduling plan.
        :param int running_instances_count: Number of instances that are currently running with this scheduling plan.
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationSchedulingQuota`.
        """
        self.max_cores = max_cores
        """:type: :class:`int`

        Maximum number of cores that can be simultaneously used with this scheduling plan.
        """
        self.running_cores_count = running_cores_count
        """:type: :class:`int`

        Number of cores that are currently running with this scheduling plan.
        """
        self.max_instances = max_instances
        """:type: :class:`int`

        Maximum number of instances that can be simultaneously used with this scheduling plan.
        """
        self.running_instances_count = running_instances_count
        """:type: :class:`int`

        Number of instances that are currently running with this scheduling plan.
        """

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationSchedulingQuota object from json describing a scheduling quota for the organization.

        :param dict json: Dictionary representing the organization scheduling plan
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationSchedulingQuota`.
        """
        if json is None:
            return None
        return cls(
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )

    def __str__(self) -> str:
        return "{}/{} instances, {}/{} cores.".format(
            self.running_instances_count, self.max_instances, self.running_cores_count, self.max_cores)

    def __repr__(self) -> str:
        return "computing_quotas.OrganizationSchedulingQuota(max_instances: {}, running_instances_count: {}, max_cores: {}, running_cores_count: {})".format(
            self.max_instances, self.running_instances_count, self.max_cores, self.running_cores_count)


class OrganizationReservedSchedulingQuota(OrganizationSchedulingQuota):
    """Describes a reserved scheduling quota for the organization.
    """

    def __init__(self, reservation_name: str, machine_key: str, max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
        """Create a new OrganizationReservedSchedulingQuota object describing a reserved scheduling quota for the organization.

        :param str machine_key: Machine key of the reservation.
        :param int max_cores: Maximum number of cores that can be simultaneously used with this reserved machine specification.
        :param int running_cores_count: Number of cores that are currently running with this reserved machine specification.
        :param int max_instances: Maximum number of instances that can be simultaneously used with this reserved machine specification.
        :param int running_instances_count: Number of instances that are currently running with this reserved machine specification.
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationReservedSchedulingQuota`.
        """
        super().__init__(max_cores, running_cores_count, max_instances, running_instances_count)
        self.machine_key = machine_key
        """:type: :class:`str`

        Machine key of the reservation.
        """
        self.reservation_name = reservation_name
        """:type: :class:`str`

        Name of the reservation.
        """

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationReservedSchedulingQuota object from json describing a reserved scheduling quota for a organization.

        :param dict json: Dictionary representing the organization reserved scheduling quota
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationReservedSchedulingQuota`.
        """
        if json is None:
            return None
        return cls(
            json.get('reservationName'),
            json.get('machineKey'),
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )

    def __str__(self) -> str:
        return "reservation '{}': {}/{} instances, {}/{} cores.".format(
            self.reservation_name, self.running_instances_count, self.max_instances, self.running_cores_count, self.max_cores)

    def __repr__(self) -> str:
        return "computing_quotas.OrganizationReservedSchedulingQuota(reservation_name: {}, machine_key: {}, max_instances: {}, " \
            "running_instances_count: {}, max_cores: {}, running_cores_count: {})".format(
                self.reservation_name, self.machine_key, self.max_instances, self.running_instances_count, self.max_cores, self.running_cores_count)


class OrganizationComputingQuotasBase(object):
    """Describes an organization's computing quotas, without organization-identifying information.
    """

    def __init__(self, flex: OrganizationSchedulingQuota, on_demand: OrganizationSchedulingQuota, reserved: Sequence[OrganizationReservedSchedulingQuota]):
        """Create a new OrganizationComputingQuotasBase object describing an organization's computing quotas.

        :param `~qarnot.computing_quotas.OrganizationSchedulingQuota` flex: Quotas for Flex scheduling plan.
        :param `~qarnot.computing_quotas.OrganizationSchedulingQuota` on_demand: Quotas for OnDemand scheduling plan.
        :param List of `~qarnot.computing_quotas.OrganizationReservedSchedulingQuota` reserved: Quotas for Reserved scheduling plan.
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationComputingQuotasBase`.
        """
        self.flex = flex
        """:type: :class:`~qarnot.computing_quotas.OrganizationSchedulingQuota`

        Quotas for Flex scheduling plan."""
        self.on_demand = on_demand
        """:type: :class:`~qarnot.computing_quotas.OrganizationSchedulingQuota`

        Quotas for OnDemand scheduling plan."""
        self.reserved = reserved
        """:type: list(:class:`~qarnot.computing_quotas.OrganizationReservedSchedulingQuota`)

        Quotas for Reserved scheduling plan."""

    @classmethod
    def _base_fields_from_json(cls, json: Dict[str, Any]):
        """Parse the flex/on_demand/reserved fields shared by every organization computing quotas variant.

        :param dict json: Dictionary representing the organization computing quota
        :returns: A tuple (flex, on_demand, reserved) ready to be passed to a subclass constructor.
        """
        return (
            OrganizationSchedulingQuota.from_json(json.get('flex')),
            OrganizationSchedulingQuota.from_json(json.get('onDemand')),
            [OrganizationReservedSchedulingQuota.from_json(v) for v in (json.get('reserved') if json.get('reserved') is not None else []) if v is not None]
        )

    def __str__(self) -> str:
        return "flex: {}, on_demand: {}, {} reserved quota(s).".format(
            self.flex, self.on_demand, len(self.reserved) if self.reserved is not None else 0
        ) + _indented_reservation_lines(self.reserved)

    def __repr__(self) -> str:
        return "computing_quotas.OrganizationComputingQuotasBase(flex: {!r}, on_demand: {!r}, reserved: {!r})".format(
            self.flex, self.on_demand, self.reserved)


class OrganizationComputingQuotas(OrganizationComputingQuotasBase):
    """Describes the organization's computing quotas.
    """

    def __init__(self, name: str, flex: OrganizationSchedulingQuota, on_demand: OrganizationSchedulingQuota, reserved: List[OrganizationReservedSchedulingQuota]):
        """Create a new OrganizationComputingQuotas object describing the organization's computing quotas.

        :param `str` name: Name of the organization.
        :param `~qarnot.computing_quotas.OrganizationSchedulingQuota` flex: Quotas for Flex scheduling plan.
        :param `~qarnot.computing_quotas.OrganizationSchedulingQuota` on_demand: Quotas for OnDemand scheduling plan.
        :param List of `~qarnot.computing_quotas.OrganizationReservedSchedulingQuota` reserved: Quotas for Reserved scheduling plan.
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationComputingQuotas`.
        """
        super().__init__(flex, on_demand, reserved)
        self.name = name
        """:type: :class:`str`

        Name of the organization."""

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationComputingQuotas object from json describing the organization's computing quotas.

        :param dict json: Dictionary representing the organization computing quota
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationComputingQuotas`.
        """
        if json is None:
            return None
        return cls(json.get('name'), *cls._base_fields_from_json(json))

    def __str__(self) -> str:
        return "organization '{}' computing quotas: flex: {}, on_demand: {}, {} reserved quota(s).".format(
            self.name, self.flex, self.on_demand, len(self.reserved) if self.reserved is not None else 0
        ) + _indented_reservation_lines(self.reserved)

    def __repr__(self) -> str:
        return "computing_quotas.OrganizationComputingQuotas(name: {}, flex: {!r}, on_demand: {!r}, reserved: {!r})".format(
            self.name, self.flex, self.on_demand, self.reserved)


class RunningCounts(object):
    """Describes running instances/cores counts for a given scheduling type.
    """

    def __init__(self, running_instances_count: int, running_cores_count: int):
        """Create a new RunningCounts object describing running instances/cores counts.

        :param int running_instances_count: Current number of running instances scheduled for the given scheduling type.
        :param int running_cores_count: Current number of running cores scheduled for the given scheduling type.
        :returns: The created :class:`~qarnot.computing_quotas.RunningCounts`.
        """
        self.running_instances_count = running_instances_count
        """:type: :class:`int`

        Current number of running instances scheduled for the given scheduling type."""
        self.running_cores_count = running_cores_count
        """:type: :class:`int`

        Current number of running cores scheduled for the given scheduling type."""

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new RunningCounts object from json describing running instances/cores counts.

        :param dict json: Dictionary representing the running counts
        :returns: The created :class:`~qarnot.computing_quotas.RunningCounts`.
        """
        if json is None:
            return None
        return cls(
            json.get('runningInstancesCount'),
            json.get('runningCoresCount'),
        )

    def __str__(self) -> str:
        return "running counts: {} instances, {} cores.".format(self.running_instances_count, self.running_cores_count)

    def __repr__(self) -> str:
        return "computing_quotas.RunningCounts(running_instances_count: {}, running_cores_count: {})".format(
            self.running_instances_count, self.running_cores_count)


class OrganizationSchedulingQuotaDetails(OrganizationSchedulingQuota):
    """Describes a scheduling quota for the organization, with the per-user running counts breakdown.
    """

    def __init__(self, running_counts_per_user: Optional[Dict[str, RunningCounts]],
                 max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
        """Create a new OrganizationSchedulingQuotaDetails object describing a scheduling quota for the organization.

        :param running_counts_per_user: Running instances/cores count of each user of the organization for this scheduling type, keyed by the user's email.
            `None` when the requester is not allowed to read the organization quota details, an empty dict when nothing is running.
        :type running_counts_per_user: Dict[`str`, `~qarnot.computing_quotas.RunningCounts`], optional
        :param int max_cores: Maximum number of cores that can be simultaneously used with this scheduling plan.
        :param int running_cores_count: Number of cores that are currently running with this scheduling plan.
        :param int max_instances: Maximum number of instances that can be simultaneously used with this scheduling plan.
        :param int running_instances_count: Number of instances that are currently running with this scheduling plan.
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationSchedulingQuotaDetails`.
        """
        super().__init__(max_cores, running_cores_count, max_instances, running_instances_count)
        self.running_counts_per_user = running_counts_per_user
        """:type: Dict[:class:`str`, :class:`~qarnot.computing_quotas.RunningCounts`], optional

        Running instances/cores count of each user of the organization for this scheduling type, keyed by the user's email.
        `None` when the requester is not allowed to read the organization quota details, an empty dict when nothing is running."""

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationSchedulingQuotaDetails object from json describing a scheduling quota for the organization.

        :param dict json: Dictionary representing the organization scheduling quota details
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationSchedulingQuotaDetails`.
        """
        if json is None:
            return None
        running_counts_per_user_json = json.get('runningCountsPerUser')
        running_counts_per_user = None
        if running_counts_per_user_json is not None:
            running_counts_per_user = {email: RunningCounts.from_json(v) for email, v in running_counts_per_user_json.items()}
        return cls(
            running_counts_per_user,
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )

    def __str__(self) -> str:
        return "{}/{} instances, {}/{} cores.".format(
            self.running_instances_count, self.max_instances, self.running_cores_count, self.max_cores)

    def __repr__(self) -> str:
        return "computing_quotas.OrganizationSchedulingQuotaDetails(max_instances: {}, running_instances_count: {}, max_cores: {}, " \
            "running_cores_count: {}, running_counts_per_user: {!r})".format(
                self.max_instances, self.running_instances_count, self.max_cores, self.running_cores_count, self.running_counts_per_user)


class OrganizationReservedSchedulingQuotaDetails(OrganizationReservedSchedulingQuota):
    """Describes a reserved scheduling quota for the organization, with the per-user running counts breakdown.
    """

    def __init__(self, running_counts_per_user: Optional[Dict[str, RunningCounts]],
                 reservation_name: str, machine_key: str, max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
        """Create a new OrganizationReservedSchedulingQuotaDetails object describing a reserved scheduling quota for the organization.

        :param running_counts_per_user: Running instances/cores count of each user of the organization on this reservation, keyed by the user's email.
            `None` when the requester is not allowed to read the organization quota details, an empty dict when nothing is running.
        :type running_counts_per_user: Dict[`str`, `~qarnot.computing_quotas.RunningCounts`], optional
        :param str machine_key: Machine key of the reservation.
        :param int max_cores: Maximum number of cores that can be simultaneously used with this reserved machine specification.
        :param int running_cores_count: Number of cores that are currently running with this reserved machine specification.
        :param int max_instances: Maximum number of instances that can be simultaneously used with this reserved machine specification.
        :param int running_instances_count: Number of instances that are currently running with this reserved machine specification.
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationReservedSchedulingQuotaDetails`.
        """
        super().__init__(reservation_name, machine_key, max_cores, running_cores_count, max_instances, running_instances_count)
        self.running_counts_per_user = running_counts_per_user
        """:type: Dict[:class:`str`, :class:`~qarnot.computing_quotas.RunningCounts`], optional

        Running instances/cores count of each user of the organization on this reservation, keyed by the user's email.
        `None` when the requester is not allowed to read the organization quota details, an empty dict when nothing is running."""

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationReservedSchedulingQuotaDetails object from json describing a reserved scheduling quota for the organization.

        :param dict json: Dictionary representing the organization reserved scheduling quota details
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationReservedSchedulingQuotaDetails`.
        """
        if json is None:
            return None
        running_counts_per_user_json = json.get('runningCountsPerUser')
        running_counts_per_user = None
        if running_counts_per_user_json is not None:
            running_counts_per_user = {email: RunningCounts.from_json(v) for email, v in running_counts_per_user_json.items()}
        return cls(
            running_counts_per_user,
            json.get('reservationName'),
            json.get('machineKey'),
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )

    def __str__(self) -> str:
        return "reservation '{}': {}/{} instances, {}/{} cores".format(
            self.reservation_name, self.running_instances_count, self.max_instances,
            self.running_cores_count, self.max_cores)

    def __repr__(self) -> str:
        return "computing_quotas.OrganizationReservedSchedulingQuotaDetails(reservation_name: {}, machine_key: {}, max_instances: {}, " \
            "running_instances_count: {}, max_cores: {}, running_cores_count: {}, running_counts_per_user: {!r})".format(
                self.reservation_name, self.machine_key, self.max_instances, self.running_instances_count,
                self.max_cores, self.running_cores_count, self.running_counts_per_user)


class OrganizationComputingQuotasDetails(OrganizationComputingQuotasBase):
    """Describes the organization's computing quotas, with the per-user running counts breakdown nested under
    each category (Flex/OnDemand/each reservation).
    """

    def __init__(self, flex: OrganizationSchedulingQuotaDetails, on_demand: OrganizationSchedulingQuotaDetails,
                 reserved: List[OrganizationReservedSchedulingQuotaDetails]):
        """Create a new OrganizationComputingQuotasDetails object describing the organization's computing quotas.

        :param `~qarnot.computing_quotas.OrganizationSchedulingQuotaDetails` flex: Quotas for Flex scheduling plan.
        :param `~qarnot.computing_quotas.OrganizationSchedulingQuotaDetails` on_demand: Quotas for OnDemand scheduling plan.
        :param List of `~qarnot.computing_quotas.OrganizationReservedSchedulingQuotaDetails` reserved: Quotas for Reserved scheduling plan.
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationComputingQuotasDetails`.
        """
        super().__init__(flex, on_demand, reserved)

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationComputingQuotasDetails object from json describing the organization's computing quotas.

        :param dict json: Dictionary representing the organization computing quota details
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationComputingQuotasDetails`.
        """
        if json is None:
            return None
        return cls(
            OrganizationSchedulingQuotaDetails.from_json(json.get('flex')),
            OrganizationSchedulingQuotaDetails.from_json(json.get('onDemand')),
            [OrganizationReservedSchedulingQuotaDetails.from_json(v) for v in (json.get('reserved') if json.get('reserved') is not None else []) if v is not None]
        )

    def __str__(self) -> str:
        return "flex: {}, on_demand: {}, {} reserved quota(s).".format(
            self.flex, self.on_demand, len(self.reserved) if self.reserved is not None else 0
        ) + _indented_reservation_lines(self.reserved)

    def __repr__(self) -> str:
        return "computing_quotas.OrganizationComputingQuotasDetails(flex: {!r}, on_demand: {!r}, reserved: {!r})".format(
            self.flex, self.on_demand, self.reserved)


class ComputingQuotas(object):
    """Describes user and organization computing quotas.
    """

    def __init__(self, user_computing_quotas: Optional[UserComputingQuotas], organization_computing_quotas: Optional[OrganizationComputingQuotas] = None):
        """Create a new ComputingQuotas object describing user and organization computing quotas.

        :param user_computing_quotas: the user related computing quotas
        :type user_computing_quotas: `~qarnot.computing_quotas.UserComputingQuotas`, optional
        :param organization_computing_quotas: the organization related computing quotas
        :type organization_computing_quotas: `~qarnot.computing_quotas.OrganizationComputingQuotas`, optional
        :returns: The created :class:`~qarnot.computing_quotas.ComputingQuotas`.
        """
        self.user = user_computing_quotas
        """:type: :class:`~qarnot.computing_quotas.UserComputingQuotas`

        The user related computing quotas."""
        self.organization = organization_computing_quotas
        """:type: :class:`~qarnot.computing_quotas.OrganizationComputingQuotas`

        The organization related computing quotas."""

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new ComputingQuotas object from json describing user and organization computing quotas.

        :param dict json: Dictionary representing the computing quotas
        :returns: The created :class:`~qarnot.computing_quotas.ComputingQuotas`
        """
        if json is None:
            return None
        user_computing_quotas = UserComputingQuotas.from_json(json.get('user'))
        organization_computing_quotas = OrganizationComputingQuotas.from_json(json.get('organization'))
        return cls(user_computing_quotas, organization_computing_quotas)

    @classmethod
    def from_json_legacy(cls, json: Dict[str, Any]):
        if json is None:
            return None
        flex = UserSchedulingQuota(json.get('maxFlexCores'), json.get('runningFlexCoreCount'), json.get('maxFlexInstances'), json.get('runningFlexInstanceCount'))
        onDemand = UserSchedulingQuota(json.get('maxOnDemandCores'), json.get('runningOnDemandCoreCount'), json.get('maxOnDemandInstances'), json.get('runningOnDemandInstanceCount'))
        user = UserComputingQuotas(flex, onDemand, [])
        return cls(user, None)

    def __str__(self) -> str:
        return "computing quotas: user: {}, organization: {}.".format(
            self.user, self.organization if self.organization is not None else "none")

    def __repr__(self) -> str:
        return "computing_quotas.ComputingQuotas(user: {!r}, organization: {!r})".format(self.user, self.organization)
