"""Retry settings that are applied to tasks in case of failure"""

from typing import Dict, Optional


class RetrySettings(object):
    """Represents task retry settings."""

    _maxTotalRetries: Optional[int] = None
    _maxPerInstanceRetries: Optional[int] = None

    def __init__(self, maxTotalRetries: Optional[int] = None, maxPerInstanceRetries: Optional[int] = None):
        """Create a new :class:`~qarnot.retry_settings.RetrySettings`.

        If neither ``maxTotalRetries`` nor ``maxPerInstanceRetries`` are set (or if they are equal to 0), the instances will not retry.
        If both ``maxTotalRetries`` and ``maxPerInstanceRetries`` are set, then the most restrictive applies.

        :param maxTotalRetries: Maximum total number of retries for the whole task. Default to None.
        :type maxTotalRetries: int | None
        :param maxPerInstanceRetries: Maximum number of retries for each task instance. Default to None.
        :type maxPerInstanceRetries: int | None
        """
        self._maxTotalRetries = maxTotalRetries
        self._maxPerInstanceRetries = maxPerInstanceRetries

    @classmethod
    def from_json(cls, json: Dict[str, int]):
        """Create the retry settings from json.

        :param dict json: Dictionary representing the retry settings
        :returns: The created :class:`~qarnot.retry_settings.RetrySettings`
        """
        maxTotalRetries: int = json["maxTotalRetries"]
        maxPerInstanceRetries: int = json["maxPerInstanceRetries"]
        return RetrySettings(maxTotalRetries, maxPerInstanceRetries)

    def to_json(self) -> Dict[str, Optional[int]]:
        """Get a dict ready to be json packed.

        :return: the json elements of the class.
        :rtype: `dict`
        """
        return {
            "maxTotalRetries": self._maxTotalRetries,
            "maxPerInstanceRetries": self._maxPerInstanceRetries
        }

    def __eq__(self, other):
        if other is None or not isinstance(other, RetrySettings):
            return False
        return self._maxTotalRetries == other._maxTotalRetries and self._maxPerInstanceRetries == other._maxPerInstanceRetries

    def __str__(self) -> str:
        return "retry settings: maxTotalRetries {}, maxPerInstanceRetries {}.".format(self._maxTotalRetries, self._maxPerInstanceRetries)

    def __repr__(self) -> str:
        return "retry_settings.RetrySettings(maxTotalRetries: {}, maxPerInstanceRetries: {})".format(self._maxTotalRetries, self._maxPerInstanceRetries)
