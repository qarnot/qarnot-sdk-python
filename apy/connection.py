"""Module describing a connection"""

from apy import get_url
from disk import QDisk
import requests

#########
# class #
#########

class QConnection(object):
    def __init__(self, qnode, auth):
        self.qnode = qnode
        self._http = requests.session()
        self._http.headers.update({"Authorization": "second"})
        #self._http.auth = auth
        self._http.verify=False #s/False/`file of auth certificates`

    def get(self, url, **kwargs):
        return self._http.get(self.qnode + url, **kwargs)

    def post(self, url, data=None, json=None,**kwargs):
        return self._http.post(self.qnode + url, json=json, **kwargs)

    def delete(self, url, data=None, json=None,**kwargs):
        return self._http.delete(self.qnode + url, **kwargs)


    #move to a better place (session)
    def disks(self):
        response = self.get(get_url('disk folder'))
        if response.status_code != 200:
            return None
        disks = [QDisk(data, self) for data in response.json()]
        return disks

    def profiles(self):
        response = self.get(get_url('list profiles'))
        if response.status_code != 200:
            return None
        return [ prof['name'] for prof in response.json()]


    def tasks(self): #todo finish when running task possible
        response = self.get(get_url('tasks'))
        if response.status_code != 200:
            print(response.status_code)
            return None
        return response.json()

##############
# Exceptions #
##############

class UnauthorizedException(Exception):
    def __init__(self, auth):
        super(UnauthorizedException, self).__init__(
            "invalid credentials : {}".format(auth))
