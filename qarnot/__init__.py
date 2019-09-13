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

__all__ = ["task", "connection", "disk", "bucket", "pool", "storage", "status"]


def raise_on_error(response):
    if response.status_code == 503:
        raise QarnotGenericException("Service Unavailable")
    if response.status_code != 200:
        try:
            raise QarnotGenericException(response.json()['message'])
        except ValueError:
            raise QarnotGenericException(response.text)


def get_url(key, **kwargs):
    """Get and format the url for the given key.
    """
    urls = {
        'disk folder': u'/disks',  # GET -> list; POST -> add
        'disk force': u'/disks/force',  # POST -> force add
        'disk info': u'/disks/{name}',  # DELETE -> remove; PUT -> update
        'get disk': u'/disks/archive/{name}.{ext}',  # GET-> disk archive
        'tree disk': u'/disks/tree/{name}',  # GET -> ls on the disk
        'link disk': u'/disks/link/{name}',  # POST -> create links
        'move disk': u'/disks/move/{name}',  # POST -> create links
        'ls disk': u'/disks/list/{name}/{path}',  # GET -> ls on the dir {path}
        'update file': u'/disks/{name}/{path}',
        # POST -> add file; GET -> download file; DELETE -> remove file; PUT -> update file settings
        'jobs': u'/jobs/',
        'job update': u'/jobs/{uuid}',  # Get->result
        'tasks': u'/tasks',  # GET -> running tasks; POST -> submit task
        'tasks summaries': u'/tasks/summaries',  # GET -> running tasks summaries;
        'task force': u'/tasks/force',  # POST -> force add
        'task update': u'/tasks/{uuid}',  # GET->result; DELETE -> abort, PATCH -> update resources
        'task snapshot': u'/tasks/{uuid}/snapshot/periodic',  # POST -> snapshots
        'task instant': u'/tasks/{uuid}/snapshot',  # POST -> get a snapshot
        'task stdout': u'/tasks/{uuid}/stdout',  # GET -> task stdout
        'task stderr': u'/tasks/{uuid}/stderr',  # GET -> task stderr
        'task abort': u'/tasks/{uuid}/abort',  # GET -> task
        'pools': u'/pools',  # GET -> pools, POST -> submit pool
        'pools summaries': u'/pools/summaries',  # GET -> pools summaries
        'pool close': u'/pools/{uuid}/close',  # POST -> close pool
        'pool update': u'/pools/{uuid}',  # GET -> pool, DELETE -> close & delete
        'user': u'/info',  # GET -> user info
        'profiles': u'/profiles',  # GET -> profiles list
        'profile details': u'/profiles/{profile}',  # GET -> profile details
        'settings': u'/settings',  # GET -> instance settings
    }
    return urls[key].format(**kwargs)


from .connection import Connection  # noqa

from ._version import get_versions  # noqa

__version__ = get_versions()['version']
del get_versions
