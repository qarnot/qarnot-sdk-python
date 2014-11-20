"""Rest API for submitting qarnot job in python"""

__all__ = ["task", "session"]

def get_url(key, **kwarg):
    """get and format the url for the given key"""
    Urls = {
        'disk folder' : '/disks' #GET -> list; POST -> add
        'disk remove' : '/disks/{name}' # DELETE  -> remove
        'get disk' : '/disks/get/{name}.{ext}' #GET-> get disk archive
        'ls disk' : '/disks/list/{name}' #GET -> ls on the disk
        'update file' : '/disks/{name}/{path}' #POST; GET; DELETE
        'list profiles': '/tasks/profiles' #GET -> possible profiles
        'tasks' : '/tasks' #GET -> runing tasks; POST -> submitt task
        'task update' : '/tasks/{id}' #GET -> result, DELETE ->abort
    }
    return Urls[key].format(**kwargs)
