from os import makedirs, path
import time
import datetime
import warnings
import sys

from . import get_url, raise_on_error, _util
from .status import Status
from .disk import Disk
from .bucket import Bucket
from .pool import Pool
from .exceptions import MissingTaskException, MaxTaskException, MaxDiskException, NotEnoughCreditsException, \
    MissingDiskException, LockedDiskException, BucketStorageUnavailableException

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

    def __init__(self, connection, name, pool = None, shortname = None, useDependencies = False):
        self.api = connection
        self.name = name
        self.shortname = shortname
        self.pool = pool
        self.poolUuid = ""
        self.state = ""
        self.uuid = ""
        self.creationDate = datetime.datetime.now()
        self.lastModified = datetime.datetime.now()
        self.useDependencies = useDependencies
        self.maxWallTime = None
        self.tasks = []
        self.constants = {}
        self.constraints = {}
        self.last_cache = time.time()

    def uri(self):
        return "jobs/" + self.uuid

    def Pool(self):
        return Pool(self.api, "original_name", "", 0)

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
            'pool': self.pool,
            'state': self.state,
            'useDependencies': self.useDependencies
        }

        return json_job

    def _update(self, json_job):
        """Update this pool from retrieved info."""
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
        self.update(True)

    def update(self, flushcache=False):
        """
        Update the pool object from the REST Api.
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

        now = time.time()

        resp = self.api._get(
            get_url('job update', uuid=self.uuid))
        if resp.status_code == 404:
            raise MissingJobException(resp.json()['message'])

        raise_on_error(resp)
        self._update(resp.json())
        self.last_cache = time.time()

    def delete(self, purge_resources=False):
        """Delete this pool on the server.

        :param bool purge_resources: parameter value is used to determine if the disk is also deleted.
                Defaults to False.

        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.MissingTaskException: pool does not exist
        """

        if self._uuid is None:
            return
        resp = self.api._delete(get_url('job update', uuid=self._uuid))
        if resp.status_code == 404:
            raise self._max_objects_exceptions_class(resp.json()['message'])
        raise_on_error(resp)
        self.state = JobState.Deleted
        self.uuid = None

        #public QJob(Connection connection, string name, QPool pool=null, string shortname=default(string), bool UseTaskDependencies=false)
            # : this (connection, new JobApi())
        #{
        #     _jobApi.Name = name;
        #     _jobApi.ShortName = shortname;
        #     if (pool != null)
        #         _jobApi.PoolUuid = pool.Uuid.ToString();
        #     _jobApi.UseDependencies = UseTaskDependencies;
        #     _uri = "jobs/" + _jobApi.ShortName;
        # }


        # public QJob(Connection connection, Guid uuid) : this(connection, new JobApi())
        # {
        #     _uri = "jobs/" + uuid.ToString();
        #     _jobApi.Uuid = uuid;
        # }

        # /// <summary>
        # /// Submit this job.
        # /// </summary>
        # /// <param name="cancellationToken">Optional token to cancel the request.</param>
        # /// <returns></returns>
        # public async Task SubmitAsync(CancellationToken cancellationToken=default(CancellationToken))
        # {
        #     if (_api.IsReadOnly) throw new Exception("Can't submit jobs, this connection is configured in read-only mode");
        #
        #     using (var response = await _api._client.PostAsJsonAsync<JobApi>("jobs", _jobApi, cancellationToken))
        #     {
        #         await Utils.LookForErrorAndThrowAsync(_api._client, response,cancellationToken);
        #         var result = await response.Content.ReadAsAsync<JobApi>(cancellationToken);
        #         await PostSubmitAsync(result, cancellationToken);
        #     }
        # }

        # /// <summary>
        # /// Update this job.
        # /// </summary>
        # /// <param name="cancellationToken">Optional token to cancel the request.</param>
        # /// <returns></returns>
        # public async Task UpdateStatusAsync(CancellationToken cancellationToken = default(CancellationToken)) {
        #     using (var response = await _api._client.GetAsync(_uri, cancellationToken))
        #     {
        #         await Utils.LookForErrorAndThrowAsync(_api._client, response, cancellationToken);
        #         var result = await response.Content.ReadAsAsync<JobApi>(cancellationToken);
        #         _jobApi = result;
        #     }
        # }

        # /// <summary>
        # /// Terminate an active job. (will cancel all remaining tasks)
        # /// </summary>
        # /// <param name="cancellationToken">Optional token to cancel the request.</param>
        # /// <returns></returns>
        # public async Task TerminateAsync(CancellationToken cancellationToken = default(CancellationToken))
        # {
        #     if (_api.IsReadOnly) throw new Exception("Can't terminate jobs, this connection is configured in read-only mode");
        #     using (var response = await _api._client.PostAsync(_uri + "/terminate", null, cancellationToken))
        #         await Utils.LookForErrorAndThrowAsync(_api._client, response, cancellationToken);
        # }

        # /// <summary>
        # /// Delete the job. If the job is active, the job is terminated and deleted.
        # /// </summary>
        # /// <param name="force">Optional boolean to force inner tasks to be deleted.</param>
        # /// <param name="cancellationToken">Optional token to cancel the request.</param>
        # /// <returns></returns>
        # public async Task DeleteAsync(bool force=false, CancellationToken cancellationToken = default(CancellationToken))
        # {
        #     if (_api.IsReadOnly) throw new Exception("Can't delete jobs, this connection is configured in read-only mode");
        #     var deleteUri = _uri;
        #     if (force)
        #         deleteUri += "?force=true";
        #     using (var response = await _api._client.DeleteAsync(deleteUri, cancellationToken))
        #         await Utils.LookForErrorAndThrowAsync(_api._client, response, cancellationToken);
        # }
        #
        # #region internals
        #
        # internal async Task PostSubmitAsync(JobApi result, CancellationToken cancellationToken = default(CancellationToken))
        #  {
        #     _jobApi.Uuid = result.Uuid;
        #     _uri = "jobs/" + _jobApi.Uuid.ToString();
        #     await UpdateStatusAsync(cancellationToken);
        # }
        # #endregion
