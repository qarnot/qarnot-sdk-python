
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

from typing import Dict, Iterable, Iterator, List, Optional

from . import get_url, raise_on_error, __version__  # type: ignore
from .hardware_constraint import HardwareConstraint
from .task import Task, BulkTaskResponse
from .pool import Pool
from .paginate import PaginateResponse, OffsetResponse
from .bucket import Bucket
from .job import Job
from ._filter import create_pool_filter, create_task_filter, create_job_filter
from ._retry import with_retry
from .exceptions import (QarnotGenericException, BucketStorageUnavailableException,
                         MissingTaskException, MissingPoolException, MissingJobException)
import requests
import warnings
import os
import boto3
import concurrent.futures
import botocore
import deprecation
from json import dumps as json_dumps
from requests.packages import urllib3
import configparser as config

#########
# class #
#########


class Connection(object):
    """Represents the couple cluster/user to which submit tasks.
    """
    def __init__(self, fileconf=None, client_token=None,
                 cluster_url=None, cluster_unsafe=False, cluster_timeout=None,
                 storage_url=None, storage_unsafe=False,
                 retry_count=5, retry_wait=1.0,
                 cluster_custom_certificate=None, storage_custom_certificate=None,
                 sanitize_bucket_paths=True, show_bucket_warnings=True):
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
        :param bool sanitize_bucket_paths: (optional) Flag to automatically sanitize bucket paths (remove extra slashes). Default to true
        :param bool show_bucket_warnings: (optional) Flag to show warnings of bucket paths sanitization. Default to true

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
        self._sanitize_bucket_paths = sanitize_bucket_paths
        self._show_bucket_warnings = show_bucket_warnings
        if fileconf is not None:
            self.storage = None
            if isinstance(fileconf, dict):
                warnings.warn("Dict config should be replaced by constructor explicit arguments.")
                self.cluster = None
                if fileconf.get('cluster_url'):
                    self.cluster = fileconf.get('cluster_url')
                auth = fileconf.get('client_auth')
                self.timeout: int = int(fileconf.get('cluster_timeout'))
                if fileconf.get('cluster_unsafe'):
                    self._http.verify = False
                elif fileconf.get('cluster_custom_certificate'):
                    self._http.verify = fileconf.get('cluster_custom_certificate')
            else:
                cfg = config.ConfigParser()
                with open(fileconf) as cfg_file:
                    cfg.read_string(cfg_file.read())

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
            urllib3.disable_warnings()

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

    @with_retry
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
        return self._http.get(self.cluster + url, timeout=self.timeout, **kwargs)

    @with_retry
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
        kwargs = Connection._prepare_json_payload(json, **(kwargs or {}))
        return self._http.patch(self.cluster + url, timeout=self.timeout, **(kwargs or {}))

    @with_retry
    def _post(self, url, json=None, **kwargs):
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
        kwargs = Connection._prepare_json_payload(json, **(kwargs or {}))
        return self._http.post(self.cluster + url, timeout=self.timeout, **kwargs)

    @with_retry
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
        return self._http.delete(self.cluster + url, timeout=self.timeout, **kwargs)

    @with_retry
    def _put(self, url, json=None, **kwargs):
        """Performs a PUT on the cluster."""
        kwargs = Connection._prepare_json_payload(json, **(kwargs or {}))
        return self._http.put(self.cluster + url, timeout=self.timeout, **kwargs)

    @staticmethod
    def _prepare_json_payload(json, **kwargs):
        if json is None:
            return kwargs

        if 'headers' not in kwargs:
            kwargs['headers'] = dict()
        kwargs['headers']['Content-Type'] = 'application/json'
        kwargs['data'] = json_dumps(json)

        return kwargs

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

    @deprecation.deprecated(deprecated_in="2.5.0", removed_in="3.0",
                            current_version=__version__,  # type: ignore
                            details="Use the all_pools function instead")
    def pools(self, summary=True, tags_intersect=None, tags=None):
        """Get the list of pools stored on this cluster for this user.

        if tags and tags_intersect are set, the connection will only return the pools with tag intersect values.
        :param bool summary: only get the summaries.
        :param tags_intersect: Desired filtering tags, all of them
        :type tags_intersect: list of :class:`str`, optional
        :param tags: Desired filtering tags, any of them
        :type tags: list of :class:`str`, optional

        :rtype: List of :class:`~qarnot.pool.Pool`.
        :returns: Pools stored on the cluster owned by the user.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details

        .. deprecated:: 2.5.0
          This function can be inefficient, Use :func:`all_pools` instead.

        """
        return list(self.all_pools(summary=summary, tags=tags, tags_intersect=tags_intersect))

    @deprecation.deprecated(deprecated_in="2.5.0", removed_in="3.0",
                            current_version=__version__,  # type: ignore
                            details="Use the all_tasks function instead")
    def tasks(self, tags=None, summary=True, tags_intersect=None):
        """Get the list of tasks stored on this cluster for this user.

        if tags and tags_intersect are set, the connection will only return the tasks with tag_intersect values.

        :param tags: Desired filtering tags, any of them
        :type tags: list of :class:`str`, optional
        :param bool summary: only get the summaries.
        :param tags_intersect: Desired filtering tags, all of them
        :type tags_intersect: list of :class:`str`, optional

        :rtype: List of :class:`~qarnot.task.Task`.
        :returns: Tasks stored on the cluster owned by the user.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details

        .. deprecated:: 2.5.0
          This function can be inefficient, Use :func:`all_tasks` instead.

        """
        return list(self.all_tasks(summary=summary, tags=tags, tags_intersect=tags_intersect))

    @deprecation.deprecated(deprecated_in="2.5.0", removed_in="3.0",
                            current_version=__version__,  # type: ignore
                            details="Use the all_jobs function instead")
    def jobs(self, tags=None, tags_intersect=None):
        """Get the list of jobs stored on this cluster for this user.

        if tags and tags_intersect are set, the connection will only return the jobs with tag intersect values.
        :param tags: Desired filtering tags, any of them
        :type tags: list of :class:`str`, optional
        :param tags_intersect: Desired filtering tags, the jobs must have all of them
        :type tags_intersect: list of :class:`str`, optional

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details

        .. deprecated:: 2.5.0
          This function can be inefficient, Use :func:`all_jobs` instead.

        """
        return list(self.all_jobs(tags=tags, tags_intersect=tags_intersect))

    def all_pools(self, summary: bool = True, tags: List[str] = None, tags_intersect: List[str] = None):
        """Get an iterator of all the pools.

        if tags and tags_intersect are set, the connection will only return the pools with tag intersect values.
        :param bool summary: only get the summaries.
        :param tags_intersect: Desired filtering tags, all of them
        :type tags_intersect: list of :class:`str`, optional
        :param tags: Desired filtering tags, any of them
        :type tags: list of :class:`str`, optional

        :rtype: List of :class:`~qarnot.pool.Pool`.
        :returns: Pools stored on the cluster owned by the user.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        return self._all_pages(self.pools_page, summary=summary, tags=tags, tags_intersect=tags_intersect)

    def all_tasks(self, summary: bool = True, tags: List[str] = None, tags_intersect: List[str] = None):
        """Get an iterator of all the tasks.

        if tags and tags_intersect are set, the connection will only return the tasks with tag_intersect values.

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
        return self._all_pages(self.tasks_page, summary=summary, tags=tags, tags_intersect=tags_intersect)

    def all_jobs(self, tags: List[str] = None, tags_intersect: List[str] = None) -> Iterator[Iterable]:
        """Get an iterator of all the jobs.

        if tags and tags_intersect are set, the connection will only return the jobs with tag intersect values.
        :param tags: Desired filtering tags, any of them
        :type tags: list of :class:`str`, optional
        :param tags_intersect: Desired filtering tags, the jobs must have all of them
        :type tags_intersect: list of :class:`str`, optional

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        return self._all_pages(self.jobs_page, tags=tags, tags_intersect=tags_intersect)

    def _all_pages(self, page_function, **kwargs) -> Iterator[Iterable]:
        """Return all the pages of an object.

        :param page_function: the call function used to retrieve a paginate list.
        :type page_function: Function
        :yield: An object
        :rtype: Iterator[Iterable]
        """

        next_token = None
        is_truncated = True
        while is_truncated:
            page = page_function(token=next_token, **kwargs)
            next_token = page.next_token
            is_truncated = page.is_truncated and next_token is not None
            for task in page.page_data:
                yield task

    def all_hardware_constraints(self) -> Iterator[Iterable]:
        """Get all the hardware constraints.

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        return self._all_offset_pages(self.hardware_constraints_page)

    def _all_offset_pages(self, page_function, **kwargs) -> Iterator[Iterable]:
        """Return all the offset pages of an object.

        :param page_function: the call function used to retrieve an offset page list.
        :type page_function: Function
        :yield: An object
        :rtype: Iterator[Iterable]
        """

        next_offset = 0
        is_truncated = True
        while is_truncated:
            page = page_function(offset=next_offset, **kwargs)
            next_offset = page.offset + page.limit
            is_truncated = page.total > next_offset
            for data in page.page_data:
                yield data

    def _paginate_request(self, filters: Dict, token: Optional[str], maximum: int) -> Dict:
        """A paginate request creator.

        :return: The json request to be call.
        :rtype: Dict
        """
        return {
            "filter": filters,
            "token": token,
            "maximumResults": maximum
        }

    def _offset_request(self, limit: int, offset: int) -> Dict:
        """An offset request creator.

        :return: The dictionary of query parameters to add to request.
        :rtype: Dict
        """
        return {
            "limit": limit,
            "offset": offset
        }

    def _offset_call(self, url, params) -> Dict:
        """Call the api and return the response body of the GET request

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details

        :return: The response body
        :rtype: Dict
        """
        response = self._get(url, params=params)
        raise_on_error(response)
        return response.json()

    def _page_call(self, url, request) -> Dict:
        """Call the api and return the response body

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details

        :return: The response body
        :rtype: Dict
        """
        response = self._post(url, request)
        raise_on_error(response)
        return response.json()

    def pools_page(self, token: Optional[str] = None, maximum: Optional[int] = None, summary: bool = True, tags: List = None, tags_intersect: List = None) -> PaginateResponse:
        """Return a paginate pool object retriver.

        :param summary: retrive a pool or a pool summary, defaults to True
        :type summary: `bool`, optional
        :param tags_intersect: use a tag exclusive filter, defaults to None
        :type tags_intersect: list of :class:`str` , optional
        :param token: the first paginate token to be used, defaults to None
        :type token: `str`, optional
        :param maximum: the maximum number of pages to retrieve, defaults to 10
        :type maximum: `int`, optional
        :return: A paginate object
        :rtype: `qarnot.paginate.PaginateResponse`
        """

        filters = create_pool_filter(tags=tags, tags_intersect=tags_intersect)
        url = get_url('paginate pools summaries') if summary and filters is None else get_url('paginate pools')
        result = self._page_call(url, self._paginate_request(filters, token, maximum))
        data = [Pool.from_json(self, pool, summary) for pool in result["data"]]
        return PaginateResponse(token=result.get("token", token), next_token=result["nextToken"], is_truncated=result["isTruncated"], page_data=data)

    def tasks_page(self, token: Optional[str] = None, maximum: Optional[int] = None, summary: bool = True, tags: List = None, tags_intersect: List = None) -> PaginateResponse:
        """Return a paginate task object.

        :param summary: retrive a task or a task summary, defaults to True
        :type summary: `bool`, optional
        :param tags_intersect: use a tag exclusive filter, defaults to None
        :type tags_intersect: list of :class:`str`, optional
        :param token: the first paginate token to be used, defaults to None
        :type token: `str`, optional
        :param maximum: the maximum number of pages to retrieve, defaults to 10
        :type maximum: `int`, optional
        :return: A paginate object
        :rtype: `qarnot.paginate.PaginateResponse`
        """

        filters = create_task_filter(tags=tags, tags_intersect=tags_intersect)
        url = get_url('paginate tasks summaries') if summary and filters is None else get_url('paginate tasks')
        result = self._page_call(url, self._paginate_request(filters, token, maximum))
        data = [Task.from_json(self, task, summary) for task in result["data"]]
        return PaginateResponse(token=result.get("token", token), next_token=result["nextToken"], is_truncated=result["isTruncated"], page_data=data)

    def jobs_page(self, token: Optional[str] = None, maximum: Optional[int] = None, tags: List = None, tags_intersect: List = None) -> PaginateResponse:
        """Return a paginate job object.

        :param tags_intersect: use a tag exclusive filter, defaults to None
        :type tags_intersect: list of :class:`str`
        :param token: the first paginate token to be used, defaults to None
        :type token: `str`, optional
        :param maximum: the maximum number of pages to retrieve, defaults to 10
        :type maximum: `int`, optional
        :return: A paginate object
        :rtype: `qarnot.paginate.PaginateResponse`
        """

        filters = create_job_filter(tags=tags, tags_intersect=tags_intersect)
        result = self._page_call(get_url('paginate jobs'), self._paginate_request(filters, token, maximum))
        data = [Job.from_json(self, job) for job in result["data"]]
        return PaginateResponse(token=result.get("token", token), next_token=result["nextToken"], is_truncated=result["isTruncated"], page_data=data)

    def hardware_constraints_page(self, limit: Optional[int] = 50, offset: Optional[int] = 0) -> OffsetResponse:
        """Return a list of hardware constraints limited with offset.

        :param limit: limit the number of displayed constraints, defaults to 50
        :type limit: `int`, optional
        :param offset: the number of constraints ignored in the response, defaults to 0
        :type token: `int`, optional
        :return: An offset object
        :rtype: `qarnot.paginate.OffsetResponse`
        """

        result = self._offset_call(get_url('hardware constraints'), self._offset_request(limit, offset))
        data = [HardwareConstraint.from_json(hw_constraint) for hw_constraint in result["data"]]
        return OffsetResponse(total=result["total"], limit=result["limit"], offset=result["offset"], page_data=data)

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

    def profiles_names(self):
        """Get list of profiles names available on the cluster.

        :rtype: list of :class:`str`

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        url = get_url('profiles')
        response = self._get(url)
        raise_on_error(response)
        return response.json()

    def profile_details(self, profile_name):
        """Get a profile available on the cluster.

        :rtype: :class:`Profile`

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        url = get_url('profile details', profile=profile_name)
        response = self._get(url)
        if response.status_code == 404:
            return None
        raise_on_error(response)
        return Profile(response.json())

    def profiles(self):
        """Get list of profiles available on the cluster.

        :rtype: list of :class:`Profile`

        :raises qarnot.exceptions.UnauthorizedException: invalid credentials
        :raises qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            return list(filter(lambda x: x is not None, executor.map(self.profile_details, self.profiles_names())))

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
        self.bucket_count = info.get('bucketCount', -1)
        """:type: :class:`int`

        Number of buckets owned by the user."""
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
        self.max_pool = info['maxPool']
        """:type: :class:`int`

        Maximum number of pool the user is allowed to create."""
        self.pool_count = info['poolCount']
        """:type: :class:`int`

        Total number of pools belonging to the user."""
        self.max_running_pool = info['maxRunningPool']
        """:type: :class:`int`

        Maximum number of running pools the user is allowed to create."""
        self.running_pool_count = info['runningPoolCount']
        """:type: :class:`int`

        Number of pools currently submitted or running."""
        self.running_instance_count = info.get('runningInstanceCount', -1)
        """:type: :class:`int`

        Number of Instances currently submitted or running."""
        self.running_core_count = info.get('runningCoreCount', -1)
        """:type: :class:`int`

        Number of cores currently submitted or running."""


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
