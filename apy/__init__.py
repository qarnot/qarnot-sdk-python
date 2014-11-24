"""Rest API for submitting qarnot job in python"""

__all__ = ["task", "connection", "disk"]

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
        'task update' : '/tasks/{id}', #GET -> result, DELETE ->abort
        'task snapshot': '/tasks/{id}/snapshot' #GET -> task snapshot
    }
    return Urls[key].format(**kwargs)
