"""Module describing a connection"""

from apy import get_url
from disk import QDisk
from task import QTask
import requests

#########
# class #
#########

class QConnection(object):
    def __init__(self, qnode, auth):
        self.qnode = qnode
        self._http = requests.session()
        self._http.headers.update({"Authorization": auth})
        self.auth = auth
        self._http.verify=False #s/False/`file of auth certificates`

    def get(self, url, **kwargs):
        ret = self._http.get(self.qnode + url, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def post(self, url, json=None,**kwargs):
        ret = self._http.post(self.qnode + url, json=json, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def delete(self, url, **kwargs):
        ret = self._http.delete(self.qnode + url, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def user_info(self):
        resp = self.get(get_url('user'))
        resp.raise_for_status()
        ret = resp.json()
        ret['disks'] = [QDisk(data, self) for data in ret['disks']]
        return ret

    #move to a better place (session)
    def disks(self):
        response = self.get(get_url('disk folder'))
        if response.status_code != 200:
            return response.status_code
        disks = [QDisk(data, self) for data in response.json()]
        return disks

    def profiles(self):
        response = self.get(get_url('list profiles'))
        if response.status_code != 200:
            return None
        return [ prof['name'] for prof in response.json()]


    def tasks(self): #todo finish when running task possible
        response = self.get(get_url('tasks'))
        response.raise_for_status()
        ret = []
        for t in response.json():
            t2 = QTask(self, "stub", None, 0)
            t2._update(t)
            ret.append(t2)
        return ret

##############
# Exceptions #
##############

class UnauthorizedException(Exception):
    def __init__(self, auth):
        super(UnauthorizedException, self).__init__(
            "invalid credentials : {}".format(auth))
