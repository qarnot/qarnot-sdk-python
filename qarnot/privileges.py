"""Privileges that can be granted by user to tasks and pools"""

from typing import Dict


class Privileges(object):
    _exportApiAndStorageCredentialsInEnvironment: bool = False  # Export the Api and Storage credentials to the task/pool environment

    def __init__(self, exportCredentialsInEnv: bool = False):
        """Create a new :class:``Privileges``"""
        self._exportApiAndStorageCredentialsInEnvironment = exportCredentialsInEnv

    @classmethod
    def from_json(cls, json: Dict[str, str]):
        """Create the privileges from json.

        :param dict json: Dictionary representing the privileges
        :returns: The created :class:``Privileges``
        """
        shouldExportCredentialsInEnvironment: bool = json["exportApiAndStorageCredentialsInEnvironment"]
        return Privileges(shouldExportCredentialsInEnvironment)

    def to_json(self) -> Dict[str, object]:
        """Get a dict ready to be json packed.
        :return: the json elements of the class.
        :rtype: `dict`
        """
        return {
            "exportApiAndStorageCredentialsInEnvironment": self._exportApiAndStorageCredentialsInEnvironment
        }

    def __eq__(self, other):
        if other is None:
            return False
        return self._exportApiAndStorageCredentialsInEnvironment == other._exportApiAndStorageCredentialsInEnvironment

    def __str__(self) -> str:
        return "privileges: exportCredentialsInEnvironnement {}.".format(self._exportApiAndStorageCredentialsInEnvironment)

    def __repr__(self) -> str:
        return "privileges.Privileges(exportCredentialsInEnv: {})".format(self._exportApiAndStorageCredentialsInEnvironment)
