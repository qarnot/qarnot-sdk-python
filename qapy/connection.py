"""Module describing a connection"""

from qapy import get_url
from disk import QDisk
from task import QTask
import requests

#########
# class #
#########

class QConnection(object):
    """represent the couple qnode/user to submit task"""
    def __init__(self, qnode, auth, timeout=None):
        """create a connection to given qnode with given credentials

        :param qnode: :class:`string`, the url of the qnode to connect to
        :param auth: :class:`string`,
          authorization of a valid user for this qnode
        :param timeout: :class:`int` how long to wait for the server response
          (for all requests)
        """
        self.qnode = qnode
        self._http = requests.session()
        self._http.headers.update({"Authorization": auth})
        self.auth = auth
        self._http.verify=False
        self.timeout = timeout

    def get(self, url, **kwargs):
        """perform a GET request on the qnode

        :param url: :class:`string`,
          relative url of the file (given the qnode url)

        :rtype: :class:`requests.Response`
        :returns: the response to the given request

        :raises:
          :exc:`UnauthorizedException`: invalid credentials

        :note: additional keyword arguments are passed to the underlying
          :attr:`requests.Session.get()`
        """
        ret = self._http.get(self.qnode + url, timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def post(self, url, json=None,**kwargs):
        """perform a POST request on the qnode

        :param url: :class:`string`,
          relative url of the file (given the qnode url)
        :param json: the data to json serialize and post

        :rtype: :class:`requests.Response`
        :returns: the response to the given request

        :raises:
          :exc:`UnauthorizedException`: invalid credentials

        :note: additional keyword arguments are passed to the underlying
          :attr:`requests.Session.post()`
        """
        ret = self._http.post(self.qnode + url, json=json,
                              timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def delete(self, url, **kwargs):
        """perform a DELETE request on the qnode

        :param url: :class:`string`,
          relative url of the file (given the qnode url)

        :rtype: :class:`requests.Response`
        :returns: the response to the given request

        :raises:
          :exc:`UnauthorizedException`: invalid credentials

        :note: additional keyword arguments are passed to the underlying
          :attr:`requests.Session.delete()`
        """
        ret = self._http.delete(self.qnode + url,
                                timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def user_info(self):
        """retrieve information of the current user on the qnode

        :rtype: dict
        :returns: a dict containing required information

        :raises:
          :exc:`UnauthorizedException`: invalid credentials

          :exc:`HTTPError`: unhandled http return code
        """
        resp = self.get(get_url('user'))
        resp.raise_for_status()
        ret = resp.json()
        ret['disks'] = [QDisk(data, self) for data in ret['disks']]
        return ret

    #move to a better place (session)
    def disks(self):
        """get the list of disks on this qnode for this user

        :rtype: list of :class:`QDisk`
        :returns: disks on the qnode owned by the user

        :raises:
          :exc:`UnauthorizedException`: invalid credentials

          :exc:`HTTPError`: unhandled http return code
        """
        response = self.get(get_url('disk folder'))
        if response.status_code != 200:
            response.raise_for_status()
        disks = [QDisk(data, self) for data in response.json()]
        return disks

    def profiles(self):
        """list availables profiles for submitting tasks

        :rtype: list of str
        :returns: list of the profile names

        :raises:
          :exc:`UnauthorizedException`: invalid credentials

          :exc:`HTTPError`: unhandled http return code
        """
        response = self.get(get_url('list profiles'))
        if response.status_code != 200:
            return None
        return [ prof['name'] for prof in response.json()]


    def tasks(self): #todo finish when running task possible
        """list tasks stored on this qnode for this user

        :rtype: list of QTask
        :returns: tasks stored on the qnode owned by the user

        :raises:
          :exc:`UnauthorizedException`: invalid credentials

          :exc:`HTTPError`: unhandled http return code
        """
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
    """Authorization given is not valid"""
    def __init__(self, auth):
        super(UnauthorizedException, self).__init__(
            "invalid credentials : {}".format(auth))
