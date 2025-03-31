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

from typing import Optional, List, Dict, Any


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


class UserReservedSchedulingQuota(UserSchedulingQuota):
    """Describes a reserved scheduling quota for the user.
    """

    def __init__(self, machine_key: str, max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
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

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new UserReservedSchedulingQuota object from json describing a reserved scheduling quota for a user.

        :param dict json: Dictionary representing the user reserved scheduling quota
        :returns: The created :class:`~qarnot.computing_quotas.UserReservedSchedulingQuota`.
        """
        if json is None:
            return None
        return cls(
            json.get('machineKey'),
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )


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
            [UserReservedSchedulingQuota.from_json(v) for v in json.get('reserved', []) if v is not None]
        )


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


class OrganizationReservedSchedulingQuota(OrganizationSchedulingQuota):
    """Describes a reserved scheduling quota for the organization.
    """

    def __init__(self, machine_key: str, max_cores: int, running_cores_count: int, max_instances: int, running_instances_count: int):
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

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationReservedSchedulingQuota object from json describing a reserved scheduling quota for a organization.

        :param dict json: Dictionary representing the organization reserved scheduling quota
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationReservedSchedulingQuota`.
        """
        if json is None:
            return None
        return cls(
            json.get('machineKey'),
            json.get('maxCores'),
            json.get('runningCoresCount'),
            json.get('maxInstances'),
            json.get('runningInstancesCount'),
        )


class OrganizationComputingQuotas(object):
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
        self.name = name
        """:type: :class:`str`

        Name of the organization."""
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
    def from_json(cls, json: Dict[str, Any]):
        """Create a new OrganizationComputingQuotas object from json describing the organization's computing quotas.

        :param dict json: Dictionary representing the organization computing quota
        :returns: The created :class:`~qarnot.computing_quotas.OrganizationComputingQuotas`.
        """
        if json is None:
            return None
        return cls(
            json.get('name'),
            OrganizationSchedulingQuota.from_json(json.get('flex')),
            OrganizationSchedulingQuota.from_json(json.get('onDemand')),
            [OrganizationReservedSchedulingQuota.from_json(v) for v in json.get('reserved', []) if v is not None]
        )


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
