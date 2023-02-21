"""Module to handle scheduling plan"""

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


class SchedulingType():
    """Represents a Scheduling Type for a compute item."""
    schedulingType: str = None

    @classmethod
    def from_string(cls, schedulingType: str):
        """Create a scheduling type from string.

        :returns: The created :class:`~qarnot.scheduling_type.SchedulingType`.
        """

        if schedulingType is None:
            return FlexScheduling()

        if schedulingType == FlexScheduling.schedulingType:
            return FlexScheduling()
        elif schedulingType == OnDemandScheduling.schedulingType:
            return OnDemandScheduling()
        elif schedulingType == ReservedScheduling.schedulingType:
            return ReservedScheduling()
        else:
            return FlexScheduling()

    def __str__(self) -> str:
        return "scheduling type {}.".format(self.schedulingType)

    def __repr__(self) -> str:
        return str(self.schedulingType)


class FlexScheduling(SchedulingType):
    """Represents a flex scheduling type, low priority & low pricing"""
    schedulingType: str = "Flex"

    def __init__(self):
        """ Create a new flex scheduling type."""


class OnDemandScheduling(SchedulingType):
    """Represents a on-demand scheduling type"""
    schedulingType: str = "OnDemand"

    def __init__(self):
        """ Create a new on-demand scheduling type."""


class ReservedScheduling(SchedulingType):
    """Represents a reserved scheduling """
    schedulingType: str = "Reserved"

    def __init__(self):
        """ Create a new reserved scheduling type."""
