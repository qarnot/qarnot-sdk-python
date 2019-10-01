import time
import datetime

from . import get_url, raise_on_error, _util
from .pool import Pool
from .exceptions import MaxDiskException, NotEnoughCreditsException, \
    MissingDiskException

try:
    from progressbar import AnimatedMarker, Bar, Percentage, AdaptiveETA, ProgressBar
except ImportError:
    pass

class JobState:
    Active = "Active"
    Terminating = "Terminating"
    Completed = "Completed"
    Deleting = "Deleting"


class MissingJobException(Exception):
    pass


class MaxJobException(Exception):
    pass


class Job(object):

    def __init__(self, connection, name, pool=None, shortname=None, useDependencies=False):
        self.api = connection
        self.name = name
        self.shortname = shortname
        self.poolUuid = None
        if pool is not None:
            self.poolUuid = pool.uuid
        self.state = ""
        self.uuid = ""
        self.creationDate = datetime.datetime.now()
        self.lastModified = datetime.datetime.now()
        self.useDependencies = useDependencies
        self.maxWallTime = None
        self.constants = {}
        self.constraints = {}
        self.last_cache = time.time()
        self._max_object_exceptions_class = MaxJobException

    def uri(self):
        return "jobs/" + self.uuid

    def _retrieve(self, connection, uuid):
        resp = connection._get(get_url('job update', uuid=uuid))
        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])
        raise_on_error(resp)
        return Pool.from_json(connection, resp.json())

    def _to_json(self):
        const_list = [
            {'key': key, 'value': value}
            for key, value in self.constants.items()
        ]
        constr_list = [
            {'key': key, 'value': value}
            for key, value in self.constraints.items()
        ]

        json_job = {
            'name': self.name,
            'constants': const_list,
            'constraints': constr_list,
            'poolUuid': self.poolUuid,
            'state': self.state,
            'useDependencies': self.useDependencies
        }

        return json_job

    def _update(self, json_job):
        """Update this job from retrieved info."""
        self.uuid = json_job['uuid']
        self.name = json_job['name']
        self.shortname = json_job.get('shortname')
        self.poolUuid = json_job.get('poolUuid')
        self.useDependencies = json_job.get('useDependencies')
        self.state = json_job['state']
        self.creation_date = _util.parse_datetime(json_job['creationDate'])
        self.lastModified = json_job.get('lastModified')
        self.maxWallTime = json_job.get('maxWallTime')

        if 'constants' in json_job:
            for constant in json_job['constants']:
                self.constants[constant.get('key')] = constant.get('value')

    def submit(self):
        if self.uuid is not None and self.uuid != "":
            return self.state
        payload = self._to_json()
        resp = self.api._post(get_url('jobs'), json=payload)

        if resp.status_code == 404:
            raise MissingDiskException(resp.json()['message'])
        elif resp.status_code == 403:
            if resp.json()['message'].startswith('Maximum number of disks reached'):
                raise MaxDiskException(resp.json()['message'])
            else:
                raise MaxJobException(resp.json()['message'])
        elif resp.status_code == 402:
            raise NotEnoughCreditsException(resp.json()['message'])
        raise_on_error(resp)
        self.uuid = resp.json()['uuid']
        self.update()

    def update(self):
        """
        Update the job object from the REST Api.
        The flushcache parameter can be used to force the update, otherwise a cached version of the object
        will be served when accessing properties of the object.
        Cache behavior is configurable with :attr:`auto_update` and :attr:`update_cache_time`.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: pool does not represent a
          valid one
        """
        if self.uuid is None:
            return

        resp = self.api._get(
            get_url('job update', uuid=self.uuid))
        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])

        raise_on_error(resp)
        self._update(resp.json())
        self.last_cache = time.time()

    def delete(self):
        """Delete this job on the server.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingJobException: job does not exist
        """

        if self.uuid is None:
            return
        resp = self.api._delete(get_url('job update', uuid=self.uuid))
        if resp.status_code == 404:
            raise self._max_objects_exceptions_class(resp.json()['message'])
        raise_on_error(resp)
        self.state = JobState.Deleting
        self.uuid = None
