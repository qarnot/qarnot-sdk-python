"""Module to handle hardware constraints"""

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

from typing import Dict
import abc


class HardwareConstraint():
    """Represents a hardware constraint."""
    _discriminator: str = None

    @classmethod
    def from_json(cls, json: Dict[str, str]):
        """Create an hardware constraint from json.

        :param qarnot.connection.Connection connection: the cluster connection
        :param dict json: Dictionary representing the constraint
        :returns: The created :class:`~qarnot.hardware_constraints.HardwareConstraint`.
        """

        discriminator: str = json["discriminator"]
        if discriminator == MinimumCoreHardware._discriminator:
            coreCount: int = json["coreCount"]
            return MinimumCoreHardware(coreCount)
        elif discriminator == MaximumCoreHardware._discriminator:
            coreCount: int = json["coreCount"]
            return MaximumCoreHardware(coreCount)
        elif discriminator == MinimumRamCoreRatioHardware._discriminator:
            minimumMemoryGBCoreRatio: float = json["minimumMemoryGBCoreRatio"]
            return MinimumRamCoreRatioHardware(minimumMemoryGBCoreRatio)
        elif discriminator == MaximumRamCoreRatioHardware._discriminator:
            maximumMemoryGBCoreRatio: float = json["maximumMemoryGBCoreRatio"]
            return MaximumRamCoreRatioHardware(maximumMemoryGBCoreRatio)
        elif discriminator == MinimumRamHardware._discriminator:
            minimumMemoryMB: float = json["minimumMemoryMB"]
            return MinimumRamHardware(minimumMemoryMB)
        elif discriminator == MaximumRamHardware._discriminator:
            maximumMemoryMB: float = json["maximumMemoryMB"]
            return MaximumRamHardware(maximumMemoryMB)
        elif discriminator == SpecificHardware._discriminator:
            specificationKey: str = json["specificationKey"]
            return SpecificHardware(specificationKey)
        elif discriminator == GpuHardware._discriminator:
            return GpuHardware()
        else:
            return None

    @abc.abstractmethod
    def to_json(self):
        """Get a dict ready to be json packed.

        :raises NotImplementedError: this is an abstract method, it should be overridden in child classes
        """


class MinimumCoreHardware(HardwareConstraint):
    """Represents an hardware constraint to limit the minimum number of cores"""
    _discriminator: str = "MinimumCoreHardwareConstraint"

    def __init__(self, coreCount: int):
        self._core_count: int = coreCount

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator,
            "coreCount": self._core_count
        }


class MaximumCoreHardware(HardwareConstraint):
    """Represents an hardware constraint to limit the maximum number of cores"""
    _discriminator: str = "MaximumCoreHardwareConstraint"

    def __init__(self, coreCount: int):
        self._core_count = coreCount

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator,
            "coreCount": self._core_count
        }


class MinimumRamCoreRatioHardware(HardwareConstraint):
    """Represents an hardware constraint to limit the minimum memory core ratio"""
    _discriminator: str = "MinimumRamCoreRatioHardwareConstraint"

    def __init__(self, ram: float):
        self._minimum_memory_gb_core_ratio = ram

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator,
            "minimumMemoryGBCoreRatio": self._minimum_memory_gb_core_ratio
        }


class MaximumRamCoreRatioHardware(HardwareConstraint):
    """Represents an hardware constraint to limit the maximum memory core ratio"""
    _discriminator: str = "MaximumRamCoreRatioHardwareConstraint"

    def __init__(self, ram: float):
        self._maximum_memory_gb_core_ratio = ram

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator,
            "maximumMemoryGBCoreRatio": self._maximum_memory_gb_core_ratio
        }


class MinimumRamHardware(HardwareConstraint):
    """Represents an hardware constraint to limit the minimum memory"""
    _discriminator: str = "MinimumRamHardwareConstraint"

    def __init__(self, ram: float):
        self._minimum_memory_mb = ram

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator,
            "minimumMemoryMB": self._minimum_memory_mb
        }


class MaximumRamHardware(HardwareConstraint):
    """Represents an hardware constraint to limit the maximum memory"""
    _discriminator: str = "MaximumRamHardwareConstraint"

    def __init__(self, ram: float):
        self._maximum_memory_mb = ram

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator,
            "maximumMemoryMB": self._maximum_memory_mb
        }


class SpecificHardware(HardwareConstraint):
    """Represents an hardware constraint to limit to a specific hardware"""
    _discriminator: str = "SpecificHardwareConstraint"

    def __init__(self, key: str):
        self._specification_key = key

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator,
            "specificationKey": self._specification_key
        }


class GpuHardware(HardwareConstraint):
    """Represents an hardware constraint to limit hardware with gpu"""
    _discriminator: str = "GpuHardwareConstraint"

    def to_json(self) -> object:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`

        """
        return {
            "discriminator": self._discriminator
        }
