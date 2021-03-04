
"""Module describing a connection."""


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

from . import get_url, raise_on_error, __version__
from .task import Task, BulkTaskResponse
from .pool import Pool
from .bucket import Bucket
from .job import Job
from ._filter import all_tag_filter
from .exceptions import (QarnotGenericException, BucketStorageUnavailableException, UnauthorizedException,
                         MissingTaskException, MissingPoolException, MissingJobException)
import requests
import sys
import warnings
import os
import time
import boto3
import botocore
from json import dumps as json_dumps
from requests.exceptions import ConnectionError
if sys.version_info[0] >= 3:  # module renamed in py3
    import configparser as config  # pylint: disable=import-error
else:
    import ConfigParser as config  # pylint: disable=import-error


#########
# class #
#########

class Connection(object):
    """Represents the couple cluster/user to which submit tasks.
    """
    def __init__(self, fileconf=None, client_token=None,
                 cluster_url=None, cluster_unsafe=False, cluster_timeout=None,
                 storage_url=None, storage_unsafe=False,
                 retry_count=5, retry_wait=1.0, cluster_custom_certificate=None, storage_custom_certificate=None):
        """Create a connection to a cluster with given config file, options or environment variables.
        Available environment variable are
        `QARNOT_CLUSTER_URL`, `QARNOT_CLUSTER_UNSAFE`, `QARNOT_CLUSTER_TIMEOUT` and `QARNOT_CLIENT_TOKEN`.

        :param fileconf: path to a qarnot configuration file or a corresponding dict
        :type fileconf: str or dict
        :param str client_token: API Token
        :param str cluster_url: (optional) Cluster url.
        :param bool cluster_unsafe: (optional) Disable certificate check
        :param int cluster_timeout: (optional) Timeout value for every request
        :param str storage_url: (optional) Storage service url.
        :param bool storage_unsafe: (optional) Disable certificate check
        :param int retry_count: (optional) ConnectionError retry count. Default to 5.
        :param float retry_wait: (optional) Retry on error wait time, progressive. (wait * (retry_count - retry_num). Default to 1s

        Configuration sample:

        .. code-block:: ini

           [cluster]
           # url of the REST API
           url=https://localhost
           # No SSL verification ?
           unsafe=False
           [client]
           # auth string of the client
           token=login
           [storage]
           url=https://storage
           unsafe=False

        """
        self._version = "qarnot-sdk-python/" + __version__
        self._http = requests.session()
        self._retry_count = retry_count
        self._retry_wait = retry_wait
        if fileconf is not None:
            self.storage = None
            if isinstance(fileconf, dict):
                warnings.warn("Dict config should be replaced by constructor explicit arguments.")
                self.cluster = None
                if fileconf.get('cluster_url'):
                    self.cluster = fileconf.get('cluster_url')
                auth = fileconf.get('client_auth')
                self.timeout = fileconf.get('cluster_timeout')
                if fileconf.get('cluster_unsafe'):
                    self._http.verify = False
                elif fileconf.get('cluster_custom_certificate'):
                    self._http.verify = fileconf.get('cluster_custom_certificate')
            else:
                cfg = config.ConfigParser()
                with open(fileconf) as cfgfile:
                    cfg.readfp(cfgfile)

                    self.cluster = None
                    if cfg.has_option('cluster', 'url'):
                        self.cluster = cfg.get('cluster', 'url')
                    if cfg.has_option('storage', 'url'):
                        self.storage = cfg.get('storage', 'url')
                    if cfg.has_option('client', 'token'):
                        auth = cfg.get('client', 'token')
                    elif cfg.has_option('client', 'auth'):
                        warnings.warn('auth is deprecated, use token instead.')
                        auth = cfg.get('client', 'auth')
                    else:
                        auth = None
                    self.timeout = None
                    if cfg.has_option('cluster', 'timeout'):
                        self.timeout = cfg.getint('cluster', 'timeout')
                    if cfg.has_option('cluster', 'unsafe') \
                       and cfg.getboolean('cluster', 'unsafe'):
                        self._http.verify = False
                    elif cfg.has_option('cluster', 'custom_certificate'):
                        self._http.verify = cfg.get('cluster', 'custom_certificate')
                    if cfg.has_option('storage', 'unsafe') \
                       and cfg.getboolean('storage', 'unsafe'):
                        storage_unsafe = True
                    if cfg.has_option('storage', 'custom_certificate'):
                        storage_custom_certificate = cfg.get('storage', 'custom_certificate')
        else:
            self.cluster = cluster_url
            self.timeout = cluster_timeout
            self._http.verify = not cluster_unsafe
            if not cluster_unsafe and cluster_custom_certificate:
                self._http.verify = cluster_custom_certificate
            self.storage = storage_url
            auth = client_token

        if not self._http.verify:
            requests.packages.urllib3.disable_warnings()

        if self.cluster is None:
            self.cluster = os.getenv("QARNOT_CLUSTER_URL")

        if self.storage is None:
            self.storage = os.getenv("QARNOT_STORAGE_URL")

        if auth is None:
            auth = os.getenv("QARNOT_CLIENT_TOKEN")

        if os.getenv("QARNOT_CLUSTER_UNSAFE") is not None:
            self._http.verify = not os.getenv("QARNOT_CLUSTER_UNSAFE") in ["true", "True", "1"]

        if os.getenv("QARNOT_CLUSTER_TIMEOUT") is not None:
            self.timeout = int(os.getenv("QARNOT_CLUSTER_TIMEOUT"))

        if auth is None:
            raise QarnotGenericException("Token is mandatory.")
        self._http.headers.update({"Authorization": auth})

        self._http.headers.update({"User-Agent": self._version})

        if self.cluster is None:
            self.cluster = "https://api.qarnot.com"

        api_settings = self._get(get_url("settings")).json()

        if self.storage is None:
            self.storage = api_settings.get("storage", "https://storage.qarnot.com")

            if self.storage is None:  # api_settings["storage"] is None
                self._s3client = None
                self._s3resource = None
                return

        user = self.user_info
        session = boto3.session.Session()
        conf = botocore.config.Config(user_agent=self._version)

        should_verify_or_certificate_path = True
        if storage_unsafe:
            should_verify_or_certificate_path = not storage_unsafe
        elif storage_custom_certificate is not None:
            should_verify_or_certificate_path = storage_custom_certificate

        self._s3client = session.client(service_name='s3',
                                        aws_access_key_id=user.email,
                                        aws_secret_access_key=auth,
                                        verify=should_verify_or_certificate_path,
                                        endpoint_url=self.storage,
                                        config=conf)
        self._s3resource = session.resource(service_name='s3',
                                            aws_access_key_id=user.email,
                                            aws_secret_access_key=auth,
                                            verify=should_verify_or_certificate_path,
                                            endpoint_url=self.storage,
                                            config=conf)

    def _get(self, url, **kwargs):
        """Perform a GET request on the cluster.

        :param str url:
          relative url of the file (according to the cluster url)

        :rtype: :class:`requests.Response`
        :returns: The response to the given request.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: Additional keyword arguments are passed to the underlying
           :func:`requests.Pool.get`.
        """

        retry = self._retry_count
        last_chance = False
        while True:
            try:
                ret = self._http.get(self.cluster + url, timeout=self.timeout,
                                     **kwargs)
                if ret.ok:
                    return ret
                if ret.status_code == 401:
                    raise UnauthorizedException()
                if 400 <= ret.status_code <= 499:
                    return ret
                if last_chance:
                    return ret
            except ConnectionError:
                if last_chance:
                    raise
            if retry > 0:
                retry -= 1
                time.sleep(self._retry_wait * (self._retry_count - retry))
            else:
                last_chance = True

    def _patch(self, url, json=None, **kwargs):
        """perform a PATCH request on the cluster

        :param url: :class:`str`,
          relative url of the file (according to the cluster url)
        :param json: the data to json serialize and post

        :rtype: :class:`requests.Response`
        :returns: The response to the given request.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: Additional keyword arguments are passed to the underlying
           :attr:`requests.Pool.post()`.
        """

        retry = self._retry_count
        last_chance = False
        while True:
            try:
                if json is not None:
                    if 'headers' not in kwargs:
                        kwargs['headers'] = dict()
                    kwargs['headers']['Content-Type'] = 'application/json'
                    kwargs['data'] = json_dumps(json)
                ret = self._http.patch(self.cluster + url,
                                       timeout=self.timeout, **kwargs)
                if ret.ok:
                    return ret
                if ret.status_code == 401:
                    raise UnauthorizedException()
                if 400 <= ret.status_code <= 499:
                    return ret
                if last_chance:
                    return ret
            except ConnectionError:
                if last_chance:
                    raise
            if retry > 0:
                retry -= 1
                time.sleep(self._retry_wait * (self._retry_count - retry))
            else:
                last_chance = True

    def _post(self, url, json=None, *args, **kwargs):
        """perform a POST request on the cluster

        :param url: :class:`str`,
          relative url of the file (according to the cluster url)
        :param json: the data to json serialize and post

        :rtype: :class:`requests.Response`
        :returns: The response to the given request.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: Additional keyword arguments are passed to the underlying
           :attr:`requests.Pool.post()`.
        """

        retry = self._retry_count
        last_chance = False
        while True:
            try:
                if json is not None:
                    if 'headers' not in kwargs:
                        kwargs['headers'] = dict()
                    kwargs['headers']['Content-Type'] = 'application/json'
                    kwargs['data'] = json_dumps(json)
                ret = self._http.post(self.cluster + url,
                                      timeout=self.timeout, *args, **kwargs)
                if ret.ok:
                    return ret
                if ret.status_code == 401:
                    raise UnauthorizedException()
                if 400 <= ret.status_code <= 499:
                    return ret
                if last_chance:
                    return ret

            except ConnectionError:
                if last_chance:
                    raise
            if retry > 0:
                retry -= 1
                time.sleep(self._retry_wait * (self._retry_count - retry))
            else:
                last_chance = True

    def _delete(self, url, **kwargs):
        """Perform a DELETE request on the cluster.

        :param url: :class:`str`,
          relative url of the file (according to the cluster url)

        :rtype: :class:`requests.Response`
        :returns: The response to the given request.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials

        .. note:: Additional keyword arguments are passed to the underlying
          :attr:`requests.Pool.delete()`.
        """

        retry = self._retry_count
        last_chance = False
        while True:
            try:
                ret = self._http.delete(self.cluster + url,
                                        timeout=self.timeout, **kwargs)
                if ret.ok:
                    return ret
                if ret.status_code == 401:
                    raise UnauthorizedException()
                if 400 <= ret.status_code <= 499:
                    return ret
                if last_chance:
                    return ret
            except ConnectionError:
                if last_chance:
                    raise
            if retry > 0:
                retry -= 1
                time.sleep(self._retry_wait * (self._retry_count - retry))
            else:
                last_chance = True

    def _put(self, url, json=None, **kwargs):
        """Performs a PUT on the cluster."""

        retry = self._retry_count
        last_chance = False
        while True:
            try:
                if json is not None:
                    if 'headers' not in kwargs:
                        kwargs['headers'] = dict()
                    kwargs['headers']['Content-Type'] = 'application/json'
                    kwargs['data'] = json_dumps(json)
                ret = self._http.put(self.cluster + url,
                                     timeout=self.timeout, **kwargs)
                if ret.ok:
                    return ret
                if ret.status_code == 401:
                    raise UnauthorizedException()
                if 400 <= ret.status_code <= 499:
                    return ret
                if last_chance:
                    return ret

            except ConnectionError:
                if last_chance:
                    raise
            if retry > 0:
                retry -= 1
                time.sleep(self._retry_wait * (self._retry_count - retry))
            else:
                last_chance = True

    @property
    def s3client(self):
        """Pre-configured s3 client object.

        :rtype: list(:class:`S3.Client`)
        :returns: A list of ObjectSummary resources
        """
        return self._s3client

    @property
    def s3resource(self):
        """Pre-configured s3 resource object.

        :rtype: list(:class:`S3.ServiceResource`)
        :returns: A list of ObjectSummary resources
        """
        return self._s3resource

    @property
    def user_info(self):
        """Get information of the current user on the cluster.

        :rtype: :class:`UserInfo`
        :returns: Requested information.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        resp = self._get(get_url('user'))
        raise_on_error(resp)
        ret = resp.json()
        return UserInfo(ret)

    def buckets(self):
        """Get the list of buckets.

        :rtype: list(class:`~qarnot.bucket.Bucket`).
        :returns: List of buckets
        """
        if self._s3client is None:
            raise BucketStorageUnavailableException()

        buckets = [Bucket(self, x.name, create=False) for x in self._s3resource.buckets.all()]
        return buckets

    def pools(self, summary=True, tags_intersect=None):
        """Get the list of pools stored on this cluster for this user.

        :param bool summary: only get the summaries.
        :param tags_intersect: Desired filtering tags, all of them
        :type tags_intersect: list of :class:`str`, optional

        :rtype: List of :class:`~qarnot.pool.Pool`.
        :returns: Pools stored on the cluster owned by the user.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        url = get_url('pools summaries') if summary else get_url('pools')

        if tags_intersect:
            tag_filter = all_tag_filter(tags_intersect)
            response = self._post(get_url('pools search'), tag_filter)
        else:
            response = self._get(url)
        raise_on_error(response)
        return [Pool.from_json(self, pool, summary) for pool in response.json()]

    def tasks(self, tags=None, summary=True, tags_intersect=None):
        """Get the list of tasks stored on this cluster for this user.

        :param tags: Desired filtering tags, any of them
        :type tags: list of :class:`str`, optional
        :param bool summary: only get the summaries.
        :param tags_intersect: Desired filtering tags, all of them
        :type tags_intersect: list of :class:`str`, optional

        :rtype: List of :class:`~qarnot.task.Task`.
        :returns: Tasks stored on the cluster owned by the user.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """

        url = get_url('tasks summaries') if summary else get_url('tasks')
        if tags_intersect:
            tag_filter = all_tag_filter(tags_intersect)
            response = self._post(get_url('tasks search'), tag_filter)
        elif tags:
            response = self._get(url, params={'tag': tags})
        else:
            response = self._get(url)
        raise_on_error(response)
        return [Task.from_json(self, task, summary) for task in response.json()]

    def jobs(self):
        """Get the list of jobs stored on this cluster for this user.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """

        response = self._get(get_url('jobs'))
        raise_on_error(response)
        return [Job.from_json(self, job) for job in response.json()]

    def retrieve_pool(self, uuid):
        """Retrieve a :class:`qarnot.pool.Pool` from its uuid

        :param str uuid: Desired pool uuid
        :rtype: :class:`~qarnot.pool.Pool`
        :returns: Existing pool defined by the given uuid
        :raises qarnot.exceptions.MissingPoolException: pool does not exist
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """

        response = self._get(get_url('pool update', uuid=uuid))
        if response.status_code == 404:
            raise MissingPoolException(response.json()['message'])
        raise_on_error(response)
        return Pool.from_json(self, response.json())

    def retrieve_task(self, uuid):
        """Retrieve a :class:`qarnot.task.Task` from its uuid

        :param str uuid: Desired task uuid
        :rtype: :class:`~qarnot.task.Task`
        :returns: Existing task defined by the given uuid
        :raises qarnot.exceptions.MissingTaskException: task does not exist
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """

        response = self._get(get_url('task update', uuid=uuid))
        if response.status_code == 404:
            raise MissingTaskException(response.json()['message'])
        raise_on_error(response)
        return Task.from_json(self, response.json())

    def retrieve_job(self, uuid):
        """Retrieve a :class:`qarnot.job.Job` from its uuid

        :param str uuid: Desired job uuid
        :rtype: :class:`~qarnot.job.Job`
        :returns: Existing job defined by the given uuid
        :raises qarnot.exceptions.MissingJobException: job does not exist
        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """

        response = self._get(get_url('job update', uuid=uuid))
        if response.status_code == 404:
            raise MissingJobException(response.json()['message'])
        raise_on_error(response)
        return Job.from_json(self, response.json())

    def retrieve_or_create_bucket(self, uuid):
        """Retrieve a :class:`~qarnot.bucket.Bucket` from its description, or create a new one.

        :param str uuid: the bucket uuid (name)
        :rtype: :class:`~qarnot.bucket.Bucket`
        :returns: Existing or newly created bucket defined by the given name
        """
        if self._s3client is None:
            raise BucketStorageUnavailableException()

        return Bucket(self, uuid)

    def retrieve_bucket(self, uuid):
        """Retrieve a :class:`~qarnot.bucket.Bucket` from its uuid (name)

        :param str uuid: Desired bucket uuid (name)
        :rtype: :class:`~qarnot.bucket.Bucket`
        :returns: Existing bucket defined by the given uuid (name)
        :raises: botocore.exceptions.ClientError: Bucket does not exist, or invalid credentials
        """
        if self._s3client is None:
            raise BucketStorageUnavailableException()

        self._s3client.head_bucket(Bucket=uuid)
        return Bucket(self, uuid, create=False)

    def create_pool(self, name, profile, instancecount=1, shortname=None):
        """Create a new :class:`~qarnot.pool.Pool`.

        :param str name: given name of the pool
        :param str profile: which profile to use with this pool
        :param instancecount: number of instances to run for the pool
        :type instancecount: int
        :param str shortname: optional unique friendly shortname of the pool
        :rtype: :class:`~qarnot.pool.Pool`
        :returns: The created :class:`~qarnot.pool.Pool`.

        .. note:: See available profiles with :meth:`profiles`.
        """
        return Pool(self, name, profile, instancecount, shortname)

    def create_elastic_pool(self, name, profile, minimum_total_slots=0, maximum_total_slots=1, minimum_idle_slots=0, minimum_idle_time_seconds=0, resize_factor=1, resize_period=90, shortname=None):
        """Create a new :class:`~qarnot.pool.Pool`.

        :param str name: given name of the pool
        :param str profile: which profile to use with this pool
        :param int minimum_total_slots: minimum number of instances to run for the pool
        :param int maximum_total_slots: maximum number of instances to run for the pool
        :param int minimum_idle_slots: the number of instances that can be idle before considering shrinking the pool
        :param int minimum_idle_time_seconds: the number of seconds before considering shrinking the pool
        :param float resize_factor: the speed with which we grow the pool to meet the demand
        :param int resize_period: the time between the load checks that decide if the pool grows or shrinks
        :param str shortname: optional unique friendly shortname of the pool
        :rtype: :class:`~qarnot.pool.Pool`
        :returns: The created :class:`~qarnot.pool.Pool`.

        .. note:: See available profiles with :meth:`profiles`.
        """
        pool = Pool(self, name, profile, shortname=shortname)
        pool.setup_elastic(minimum_total_slots, maximum_total_slots, minimum_idle_slots, minimum_idle_time_seconds, resize_factor, resize_period)
        return pool

    def create_task(self, name, profile_or_pool=None, instancecount_or_range=1, shortname=None, job=None):
        """Create a new :class:`~qarnot.task.Task`.

        :param str name: given name of the task
        :param profile_or_pool: which profile to use with this task, or which Pool to run task, or which job to attach it to
        :type profile_or_pool: str or :class:`~qarnot.pool.Pool` or None
        :param instancecount_or_range: number of instances, or ranges on which to run task. Defaults to 1.
        :type instancecount_or_range: int or str
        :param str shortname: optional unique friendly shortname of the task
        :rtype: :class:`~qarnot.task.Task`
        :returns: The created :class:`~qarnot.task.Task`.
        :param job: which job to attach the task to
        :type job: :class:`~qarnot.job.Job`

        .. note:: See available profiles with :meth:`profiles`.
        """
        return Task(self, name, profile_or_pool, instancecount_or_range, shortname, job)

    def submit_tasks(self, tasks):
        """Submit a list of :class:`~qarnot.task.Task`.

        :param List of :class:`~qarnot.task.Task`.
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details

        .. note:: Will ensure all added files are on the resource bucket
           regardless of their uploading mode.
        """
        error_message = ""

        for task in tasks:
            task._pre_submit()

        payload = [task._to_json() for task in tasks]
        responses = self._post(get_url('tasks'), json=payload)

        if responses.status_code == 503:
            raise QarnotGenericException("Service Unavailable")

        bulk_responses = [BulkTaskResponse(x) for x in responses.json()]

        # The contract with the API is that the response list and the request list should be in the same order
        for i, response in enumerate(bulk_responses):
            if not response.is_success():
                error_message += "[{0}] : {1}, {2}\n".format(tasks[i], response.status_code, response.message)
            else:
                tasks[i]._uuid = response.uuid
                tasks[i]._post_submit()

        if error_message:
            raise QarnotGenericException(error_message)

    def profiles(self):
        """Get list of profiles available on the cluster.

        :rtype: list of :class:`Profile`

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """

        url = get_url('profiles')
        response = self._get(url)
        raise_on_error(response)
        profiles_list = []
        for p in response.json():
            url = get_url('profile details', profile=p)
            response2 = self._get(url)
            if response2.status_code == 404:
                continue
            raise_on_error(response2)
            profiles_list.append(Profile(response2.json()))
        return profiles_list

    def retrieve_profile(self, name):
        """Get details of a profile from its name.

        :rtype: :class:`Profile`

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """

        url = get_url('profile details', profile=name)
        response = self._get(url)
        raise_on_error(response)
        if response.status_code == 404:
            raise QarnotGenericException(response.json()['message'])
        return Profile(response.json())

    def create_bucket(self, name):
        """Create a new :class:`~qarnot.bucket.Bucket`.
        If the bucket already exist, retrieve the existing bucket.

        :param str name: bucket name

        :rtype: :class:`qarnot.bucket.Bucket`
        :returns: The created or existing :class:`~qarnot.bucket.Bucket`.

        """
        return Bucket(self, name)

    def create_job(self, name, pool=None, shortname=None, useDependencies=False):
        """Create a new :class:`~qarnot.job.Job`.

        :param name: given name of the job
        :type name: :class:`str`
        :param pool: which Pool to submit the job in,
        :type pool: :class:`~qarnot.pool.Pool` or None
        :param shortname: userfriendly job name
        :type shortname: :class:`str`
        :param use_dependencies: allow dependencies between tasks in this job
        :type job: :class:`bool`

        :returns: The created :class:`~qarnot.job.Job`.
        """
        return Job(self, name, pool, shortname, useDependencies)

###################
# utility Classes #
###################


class UserInfo(object):
    """Information about a qarnot user."""

    def __init__(self, info):
        self.email = info.get('email', '')
        """:type: :class:`str`

        User email address."""
        self.max_bucket = info['maxBucket']
        """:type: :class:`int`

        Maximum number of buckets allowed (resource and result buckets)."""
        self.quota_bytes_bucket = info['quotaBytesBucket']
        """:type: :class:`int`

        Total storage space allowed for the user's buckets (in Bytes)."""
        self.used_quota_bytes_bucket = info['usedQuotaBytesBucket']
        """:type: :class:`int`

        Total storage space used by the user's buckets (in Bytes)."""
        self.task_count = info['taskCount']
        """:type: :class:`int`

        Total number of tasks belonging to the user."""
        self.max_task = info['maxTask']
        """:type: :class:`int`

        Maximum number of tasks the user is allowed to create."""
        self.running_task_count = info['runningTaskCount']
        """:type: :class:`int`

        Number of tasks currently in 'Submitted' state."""
        self.max_running_task = info['maxRunningTask']
        """:type: :class:`int`

        Maximum number of running tasks."""
        self.max_instances = info['maxInstances']
        """:type: :class:`int`

        Maximum number of instances."""


class Profile(object):
    """Information about a profile."""
    def __init__(self, info):
        self.name = info['name']
        """:type: :class:`str`

        Name of the profile."""
        self.constants = tuple((cst['name'], cst['value'])
                               for cst in info['constants'])
        """:type: List of (:class:`str`, :class:`str`)

        List of couples (name, value) representing constants for this profile
        and their default values."""

    def __repr__(self):
        return 'Profile(name=%s, constants=%r}' % (self.name, self.constants)
