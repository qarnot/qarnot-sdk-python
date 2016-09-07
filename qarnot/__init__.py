"""Rest API for submitting qarnot jobs in Python."""


# Copyright 2016 Qarnot computing
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


__all__ = ["task", "connection", "disk", "notification"]


class QarnotException(Exception):
    """General Connection exception"""
    def __init__(self, msg):
        super(QarnotException, self).__init__("Error : {0}".format(msg))


def raise_on_error(response):
    if response.status_code == 503:
        raise QarnotException("Service Unavailable")
    if response.status_code != 200:
        try:
            raise QarnotException(response.json()['message'])
        except ValueError:
            raise QarnotException(response.text)


def get_url(key, **kwargs):
    """Get and format the url for the given key.
    """
    urls = {
        'disk folder': '/disks',  # GET -> list; POST -> add
        'global disk folder': '/disks/global',  # GET -> list
        'disk force': '/disks/force',  # POST -> force add
        'disk info': '/disks/{name}',  # DELETE -> remove; PUT -> update
        'get disk': '/disks/archive/{name}.{ext}',  # GET-> disk archive
        'tree disk': '/disks/tree/{name}',  # GET -> ls on the disk
        'link disk': '/disks/link/{name}',  # POST -> create links
        'ls disk': '/disks/list/{name}/{path}',  # GET -> ls on the dir {path}
        'update file': '/disks/{name}/{path}',  # POST -> add file; GET -> download file; DELETE -> remove file; PUT -> update file settings
        'tasks': '/tasks',  # GET -> running tasks; POST -> submit task
        'task force': '/tasks/force',  # POST -> force add
        'task update': '/tasks/{uuid}',  # GET->result; DELETE -> abort, PATCH -> update resources
        'task snapshot': '/tasks/{uuid}/snapshot/periodic',  # POST -> snapshots
        'task instant': '/tasks/{uuid}/snapshot',  # POST -> get a snapshot
        'task stdout': '/tasks/{uuid}/stdout',  # GET -> task stdout
        'task stderr': '/tasks/{uuid}/stderr',  # GET -> task stderr
        'task abort': '/tasks/{uuid}/abort',  # GET -> task stderr
        'user': '/info',  # GET -> user info
        'notification': '/notifications',  # GET -> notifications list; POST -> add notification
        'notification update': '/notifications/{uuid}'  # GET -> notification info; DELETE -> remove notification; PUT -> update
    }
    return urls[key].format(**kwargs)

from qarnot.connection import Connection  # noqa

from ._version import get_versions  # noqa
__version__ = get_versions()['version']
del get_versions
