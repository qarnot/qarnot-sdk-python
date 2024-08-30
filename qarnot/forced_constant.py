from typing import Optional, Union, Dict
from enum import Enum


class ForcedConstantAccess(Enum):
    ReadWrite = "ReadWrite"
    ReadOnly = "ReadOnly"


class ForcedConstant(object):
    """Forced Constant Information

    .. note:: For internal usage only
    """

    def __init__(self, forced_value: str, force_export_in_environment: Optional[bool] = None, access: Optional[ForcedConstantAccess] = None):
        self.forced_value = forced_value
        """:type: :class:`str`

        Forced value for the constant."""

        self.force_export_in_environment = force_export_in_environment
        """:type: :class:`bool`

        Whether the constant should be forced in the execution environment or not."""

        self.access = access
        """:type: :class:`~qarnot.forced_constant.ForcedConstantAccess`

        The access level of the constant: ReadOnly or ReadWrite."""

    def to_json(self, name: str):
        result: Dict[str, Union[str, bool]] = {
            "constantName": name,
            "forcedValue": self.forced_value,
        }

        if self.force_export_in_environment is not None:
            result["forceExportInEnvironment"] = self.force_export_in_environment

        if self.access is not None:
            result["access"] = self.access.value

        return result
