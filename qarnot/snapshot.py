"""Module to handle snapshot"""

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

from datetime import datetime
from typing import Optional, Dict, Any


class SnapshotConfiguration():
    """Configuration used for a task snapshot"""

    _whitelist: Optional[str] = None
    _blacklist: Optional[str] = None
    _bucket_name: Optional[str] = None
    _bucket_prefix: Optional[str] = None

    def __init__(self,
                 whitelist: Optional[str] = None,
                 blacklist: Optional[str] = None,
                 bucket_name: Optional[str] = None,
                 bucket_prefix: Optional[str] = None):
        """The SnapshotConfiguration constructor.

        :param str whitelist: Whitelist filter for the snapshot.
        :param str blacklist: Blacklist filter for the snapshot.
        :param str bucket_name: Name of the bucket in which to upload the snapshot.
        :param str bucket_prefix: Prefix added to the files uploaded for the snapshot.
        :returns: The created :class:`~qarnot.snapshot.SnapshotConfiguration`.
        """
        self._whitelist = whitelist
        self._blacklist = blacklist
        self._bucket_name = bucket_name
        self._bucket_prefix = bucket_prefix

    def to_json(self) -> Dict[str, Optional[str | int]]:
        """Get a SnapshotConfiguration ready to be json packed.

        :return: the json representation of a snapshot configuration.
        :rtype: Dict[str, Optional[str|int]]
        """
        return {
            "whitelist": self._whitelist,
            "blacklist": self._blacklist,
            "bucket": self._bucket_name,
            "bucketPrefix": self._bucket_prefix
        }

    @classmethod
    def from_json(cls, json: Dict[str, Optional[str]]):
        """Create a SnapshotConfiguration from a json representation

        :param json: the json to use to create the SnapshotConfiguration object.
        :type json: `Dict[str, Optional[str]]`
        :returns: The created :class:`~qarnot.snapshot.SnapshotConfiguration`.
        """
        if json is None:
            return None

        whitelist = json.get("whitelist")
        blacklist = json.get("blacklist")
        bucket_name = json.get("bucket")
        bucket_prefix = json.get("bucketPrefix")

        return SnapshotConfiguration(whitelist, blacklist, bucket_name, bucket_prefix)


class PeriodicSnapshotConfiguration(SnapshotConfiguration):
    """Configuration used for a task periodic snapshot"""
    _interval: int = None

    def __init__(self,
                 interval: int,
                 whitelist: Optional[str] = None,
                 blacklist: Optional[str] = None,
                 bucket_name: Optional[str] = None,
                 bucket_prefix: Optional[str] = None):
        """The PeriodicSnapshotConfiguration constructor.

        :param int interval: Interval (in seconds) between two periodic snapshots.
        :param str whitelist: Whitelist filter for the snapshot.
        :param str blacklist: Blacklist filter for the snapshot.
        :param str bucket_name: Bucket where to upload the snapshot.
        :param str bucket_prefix: Prefix added to the files uploaded for the snapshot.
        :returns: The created :class:`~qarnot.snapshot.SnapshotConfiguration`.
        """
        super().__init__(whitelist, blacklist, bucket_name, bucket_prefix)
        self._interval = interval

    def to_json(self) -> Dict[str, Optional[str | int]]:
        """Get a PeriodicSnapshotConfiguration ready to be json packed.

        :return: the json representation of a periodic snapshot configuration.
        :rtype: Dict[str, Optional[str|int]]
        """
        json: Dict[str, Optional[str | int]] = super().to_json()
        json["interval"] = int(self._interval)
        return json


class SnapshotStatus():
    """Represents a Snapshot of a task."""
    status: str = None
    is_completed: bool = False

    @classmethod
    def from_string(cls, status: str):
        """Create a snapshot status from string.

        :returns: The created :class:`~qarnot.snapshot.SnapshotStatus`.
        """

        if status is None:
            return TriggeredStatus()

        status = str(status)

        if status.lower() == TriggeredStatus.status.lower():
            return TriggeredStatus()
        elif status.lower() == InProgressStatus.status.lower():
            return InProgressStatus()
        elif status.lower() == SuccessStatus.status.lower():
            return SuccessStatus()
        elif status.lower() == FailedStatus.status.lower():
            return FailedStatus()
        else:
            return TriggeredStatus()

    def __str__(self) -> str:
        return "snapshot status {}.".format(self.status)

    def __repr__(self) -> str:
        return str(self.status)


class TriggeredStatus(SnapshotStatus):
    """Represents a snapshot triggered status """
    status: str = "Triggered"
    is_completed: bool = False

    def __init__(self):
        """ Create a new snapshot triggered status."""


class InProgressStatus(SnapshotStatus):
    """Represents a snapshot in progress status"""
    status: str = "InProgress"
    is_completed: bool = False

    def __init__(self):
        """ Create a new snapshot in progress status."""


class SuccessStatus(SnapshotStatus):
    """Represents a snapshot success status"""
    status: str = "Success"
    is_completed: bool = True

    def __init__(self):
        """ Create a new snapshot success status."""


class FailedStatus(SnapshotStatus):
    """Represents snapshot failed status"""
    status: str = "Failure"
    is_completed: bool = True

    def __init__(self):
        """ Create a new snapshot failed status."""


class Snapshot():
    """Represents a Snapshot of a task."""
    _id: str = None
    _task_uuid: str = None
    _trigger_date: datetime = None
    _last_update_date: Optional[datetime] = None
    _snapshot_config: SnapshotConfiguration = None
    _status: SnapshotStatus = None
    _size_to_upload: Optional[int] = None
    _transferred_size: Optional[int] = None

    def __init__(self,
                 uid: str = None,
                 task_uuid: str = None,
                 trigger_date: datetime = None,
                 last_update_date: Optional[datetime] = None,
                 snapshot_config: SnapshotConfiguration = None,
                 status: SnapshotStatus = None,
                 size_to_upload: Optional[int] = None,
                 transferred_size: Optional[int] = None):
        """The Snapshot constructor.

        :param str uid: identifier of the snapshot.
        :param str task_uuid: identifier of the task hat have been snapshoted.
        :param datetime trigger_date: the date (utc) when the snapshot was requested.
        :param datetime last_update_date: date (utc) of the last update of the current state of the snapshot.
        :param `~qarnot.snapshot.SnapshotConfiguration` snapshot_config: the filter and output configuration of the snapshot.
        :param `~qarnot.snapshot.SnapshotStatus` status: Current progress status of the snapshot.
        :param int size_to_upload: total size (in bytes) expected to upload for the snapshot.
        :param int transferred_size: current size (in bytes) of the upload for the snapshot.
        :returns: The created :class:`~qarnot.snapshot.Snapshot`.
        """
        self._id = uid
        self._task_uuid = task_uuid
        self._trigger_date = trigger_date
        self._last_update_date = last_update_date
        self._snapshot_config = snapshot_config
        self._status = status
        self._size_to_upload = size_to_upload
        self._transferred_size = transferred_size

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a Snapshot from a json representation

        :param json: the json to use to create the Snapshot object.
        :type json: `Dict[str, Any]`
        :returns: The created :class:`~qarnot.snapshot.Snapshot`.
        """
        if json is None:
            return None

        uid = json.get("id")
        task_uuid = json.get("taskUuid")
        trigger_date = json.get("triggerDate")
        last_update_date = json.get("lastUpdateDate")
        snapshot_config = SnapshotConfiguration.from_json(json.get("snapshotConfig"))
        status = SnapshotStatus.from_string(json.get("status"))
        size_to_upload = json.get("sizeToUpload")
        transferred_size = json.get("transferredSize")

        return Snapshot(uid, task_uuid, trigger_date, last_update_date, snapshot_config, status, size_to_upload, transferred_size)
