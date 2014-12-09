"""Rest API for submitting qarnot jobs in python"""

__all__ = ["task", "connection", "disk"]

__version__ = '0.0.1'

def get_url(key, **kwargs):
    """get and format the url for the given key"""
    Urls = {
        'disk folder' : '/disks', #GET -> list; POST -> add
        'disk info' : '/disks/{name}', # DELETE  -> remove
        'get disk' : '/disks/get/{name}.{ext}', #GET-> disk archive
        'ls disk' : '/disks/list/{name}', #GET -> ls on the disk
        'update file' : '/disks/{name}/{path}', #POST; GET; DELETE
        'list profiles': '/tasks/profiles', #GET -> possible profiles
        'tasks' : '/tasks', #GET -> runing tasks; POST -> submit task
        'task update' : '/tasks/{uuid}', #GET->result, DELETE->abort
        'task snapshot': '/tasks/{uuid}/snapshot', #POST -> snapshot
        'task stdout': '/tasks/{uuid}/stdout', #GET -> task stdout
        'task stderr': '/tasks/{uuid}/stderr', #GET -> task stderr
        'user': '/info' #GET -> user info
    }
    return Urls[key].format(**kwargs)

from connection import QConnection
from task import QTask
