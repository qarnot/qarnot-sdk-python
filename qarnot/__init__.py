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


from .exceptions import QarnotGenericException

__all__ = ["task", "connection", "bucket", "pool",
           "storage", "status", "job", "advanced_bucket", "hardware_constraint"]


def raise_on_error(response):
    if response.status_code == 503:
        raise QarnotGenericException("Service Unavailable")
    if response.status_code < 200 or response.status_code >= 300:
        try:
            raise QarnotGenericException(response.json()['message'])
        except ValueError as value:
            raise QarnotGenericException(response.text) from value


def get_url(key, **kwargs):
    """Get and format the url for the given key.
    """
    urls = {
        'jobs': u'/jobs/',  # POST -> Submit Job
        'paginate jobs': u'/jobs/paginate',  # GET -> paginate jobs
        'job update': u'/jobs/{uuid}',  # GET -> result; DELETE -> abort
        'job delete': u'/jobs/{uuid}?force={force}',  # DELETE -> delete job
        'jobs search': u'/jobs/search',  # POST -> make a custom search on jobs
        'job terminate': u'/jobs/{uuid}/terminate',  # POST -> terminate a job
        'job tasks': u'/jobs/{uuid}/tasks',  # GET -> tasks in job
        'tasks': u'/tasks',  # POST -> submit task
        'paginate tasks': u'/tasks/paginate',  # GET -> paginate tasks
        'paginate tasks summaries': u'/tasks/summaries/paginate',  # GET -> paginate tasks summaries;
        'tasks search': u'/tasks/search',  # POST -> make a custom search on tasks
        'task force': u'/tasks/force',  # POST -> force add
        'task update': u'/tasks/{uuid}',  # GET->result; DELETE -> abort, PATCH -> update resources
        'task snapshot': u'/tasks/{uuid}/snapshot/periodic',  # POST -> snapshots
        'task instant': u'/tasks/{uuid}/snapshot',  # POST -> get a snapshot
        'task stdout': u'/tasks/{uuid}/stdout',  # GET -> task stdout
        'task stderr': u'/tasks/{uuid}/stderr',  # GET -> task stderr
        'task abort': u'/tasks/{uuid}/abort',  # GET -> task
        'pools': u'/pools',  # POST -> submit pool
        'paginate pools': u'/pools/paginate',  # GET -> paginate pools
        'paginate pools summaries': u'/pools/summaries/paginate',  # GET -> paginate pools summaries
        'pools search': u'/pools/search',  # POST -> make a custom search on pools
        'pool close': u'/pools/{uuid}/close',  # POST -> close pool
        'pool update': u'/pools/{uuid}',  # GET -> pool, DELETE -> close & delete, PATCH -> update resources
        'pool stdout': u'/pools/{uuid}/stdout',  # GET -> pool stdout
        'pool stderr': u'/pools/{uuid}/stderr',  # GET -> pool stderr
        'user': u'/info',  # GET -> user info
        'profiles': u'/profiles',  # GET -> profiles list
        'profile details': u'/profiles/{profile}',  # GET -> profile details
        'hardware constraints': u'/hardware-constraints',  # GET -> user hardware constraints list
        'settings': u'/settings',  # GET -> instance settings
    }
    return urls[key].format(**kwargs)


from ._version import get_versions  # noqa
__version__ = get_versions()['version']  # type: ignore
del get_versions

from .connection import Connection  # noqa
