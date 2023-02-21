"""Rest API for submitting qarnot jobs in Python."""


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


from .exceptions import QarnotGenericException, UnauthorizedException
from ._util import get_error_message_from_http_response

__all__ = ["task", "connection", "bucket", "pool",
           "storage", "status", "job", "advanced_bucket", "hardware_constraint", "scheduling_type"]


def raise_on_error(response):
    if response.status_code == 503:
        raise QarnotGenericException("Service Unavailable")
    if response.status_code == 403:
        raise UnauthorizedException(get_error_message_from_http_response(response))
    if response.status_code < 200 or response.status_code >= 300:
        try:
            raise QarnotGenericException(get_error_message_from_http_response(response, True))
        except ValueError as value:
            raise QarnotGenericException(response.text) from value


def get_url(key, **kwargs):
    """Get and format the url for the given key.
    """
    urls = {
        'jobs': '/jobs/',  # POST -> Submit Job
        'paginate jobs': '/jobs/paginate',  # GET -> paginate jobs
        'job update': '/jobs/{uuid}',  # GET -> result; DELETE -> abort
        'job delete': '/jobs/{uuid}?force={force}',  # DELETE -> delete job
        'jobs search': '/jobs/search',  # POST -> make a custom search on jobs
        'job terminate': '/jobs/{uuid}/terminate',  # POST -> terminate a job
        'job tasks': '/jobs/{uuid}/tasks',  # GET -> tasks in job
        'tasks': '/tasks',  # POST -> submit task
        'paginate tasks': '/tasks/paginate',  # GET -> paginate tasks
        'paginate tasks summaries': '/tasks/summaries/paginate',  # GET -> paginate tasks summaries;
        'tasks search': '/tasks/search',  # POST -> make a custom search on tasks
        'task force': '/tasks/force',  # POST -> force add
        'task update': '/tasks/{uuid}',  # GET->result; DELETE -> abort, PATCH -> update resources
        'task snapshot': '/tasks/{uuid}/snapshot/periodic',  # POST -> snapshots
        'task instant': '/tasks/{uuid}/snapshot',  # POST -> get a snapshot
        'task stdout': '/tasks/{uuid}/stdout',  # GET -> task stdout
        'task stderr': '/tasks/{uuid}/stderr',  # GET -> task stderr
        'task instance stdout': '/tasks/{uuid}/stdout/{instanceId}',  # GET -> task instance stdout
        'task instance stderr': '/tasks/{uuid}/stderr/{instanceId}',  # GET -> task instance stderr
        'task abort': '/tasks/{uuid}/abort',  # GET -> task
        'pools': '/pools',  # POST -> submit pool
        'paginate pools': '/pools/paginate',  # GET -> paginate pools
        'paginate pools summaries': '/pools/summaries/paginate',  # GET -> paginate pools summaries
        'pools search': '/pools/search',  # POST -> make a custom search on pools
        'pool close': '/pools/{uuid}/close',  # POST -> close pool
        'pool update': '/pools/{uuid}',  # GET -> pool, DELETE -> close & delete, PATCH -> update resources
        'pool stdout': '/pools/{uuid}/stdout',  # GET -> pool stdout
        'pool stderr': '/pools/{uuid}/stderr',  # GET -> pool stderr
        'pool instance stdout': '/pools/{uuid}/stdout/{instanceId}',  # GET -> pool instance stdout
        'pool instance stderr': '/pools/{uuid}/stderr/{instanceId}',  # GET -> pool instance stderr
        'user': '/info',  # GET -> user info
        'profiles': '/profiles',  # GET -> profiles list
        'profile details': '/profiles/{profile}',  # GET -> profile details
        'hardware constraints': '/hardware-constraints',  # GET -> user hardware constraints list
        'cpu model constraints search': '/hardware-constraints/cpu-model-constraints/search',  # GET -> user hardware constraints list
        'settings': '/settings',  # GET -> instance settings
    }
    return urls[key].format(**kwargs)


from ._version import get_versions  # noqa
__version__ = get_versions()['version']  # type: ignore
del get_versions

from .connection import Connection  # noqa
