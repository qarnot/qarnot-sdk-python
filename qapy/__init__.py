"""Rest API for submitting qarnot jobs in python"""

__all__ = ["task", "connection", "disk"]

__version__ = '0.0.1'

def get_url(key, **kwargs):
    """get and format the url for the given key"""
    urls = {
        'disk folder' : '/disks', #GET -> list; POST -> add
        'disk force' : '/disks/force', # POST -> force add
        'disk info' : '/disks/{name}', # DELETE  -> remove #PUT -> update
        'get disk' : '/disks/archive/{name}.{ext}', #GET-> disk archive
        'tree disk' : '/disks/tree/{name}', #GET -> ls on the disk
        'ls disk': '/disks/list/{name}/{path}', #GET -> ls on the dir {path}
        'update file' : '/disks/{name}/{path}', #POST; GET; DELETE
        'list profiles': '/tasks/profiles', #GET -> possible profiles
        'get profile' : '/tasks/profiles/{name}', #GET -> profile info
        'tasks' : '/tasks', #GET -> runing tasks; POST -> submit task
        'task force' : '/tasks/force', #POST -> force add
        'task update' : '/tasks/{uuid}', #GET->result, DELETE->abort
        'task snapshot': '/tasks/{uuid}/snapshot/periodic', #POST -> snapshots
        'task instant' : '/tasks/{uuid}/snapshot', #POST-> get a snapshot
        'task stdout': '/tasks/{uuid}/stdout', #GET -> task stdout
        'task stderr': '/tasks/{uuid}/stderr', #GET -> task stderr
        'user': '/info' #GET -> user info
    }
    return urls[key].format(**kwargs)

import qapy.connection

QApy = qapy.connection.QApy
