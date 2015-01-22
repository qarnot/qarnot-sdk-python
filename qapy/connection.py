"""Module describing a connection"""

from qapy import get_url
from qapy.disk import QDisk
from qapy.task import QTask
import requests
import sys

if sys.version_info[0] >= 3: # module renamed in py3
    import configparser as config
else:
    import ConfigParser as config


#########
# class #
#########

class QApy(object):
    """represent the couple cluster/user to submit task

    .. automethod:: __init__
    """
    def __init__(self, conf):
        """create a connection to a cluster with given config file or
        dictionnary

        :param conf: path to a qarnot configuration file or dictionnary
          containing corresponding keys as follow:
          for variable var of section s key is 's_var'
        """
        self._http = requests.session()
        self._http.verify = False

        if isinstance(conf, dict):
            self.cluster = conf['cluster_url']
            self._http.headers.update({"Authorization": conf['client_auth']})
            print(self._http.headers)
            self.auth = conf['client_auth']
            print (self.cluster)
            self.timeout = conf.get('cluster_timeout')
        else:
            cfg = config.ConfigParser()
            with open(conf) as cfgfile:
                cfg.readfp(cfgfile)

                self.cluster = cfg.get('cluster', 'url')
                self._http.headers.update({"Authorization": cfg.get('client',
                                                                    'auth')})
                self.auth = cfg.get('client', 'auth')
                self.timeout = None
                if cfg.has_option('cluster', 'timeout'):
                    self.timeout = cfg.getint('cluster', 'timeout')

    def _get(self, url, **kwargs):
        """perform a GET request on the cluster

        :param str url:
          relative url of the file (given the cluster url)

        :rtype: :class:`requests.Response`
        :returns: the response to the given request

        :raises UnauthorizedException: invalid credentials

        .. note:: additional keyword arguments are passed to the underlying
           :func:`requests.Session.get`
        """
        ret = self._http.get(self.cluster + url, timeout=self.timeout,
                             **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def _post(self, url, json=None, **kwargs):
        """perform a POST request on the cluster

        :param url: :class:`string`,
          relative url of the file (given the cluster url)
        :param json: the data to json serialize and post

        :rtype: :class:`requests.Response`
        :returns: the response to the given request

        :raises UnauthorizedException: invalid credentials

        .. note:: additional keyword arguments are passed to the underlying
           :attr:`requests.Session.post()`
        """
        ret = self._http.post(self.cluster + url, json=json,
                              timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def _delete(self, url, **kwargs):
        """perform a DELETE request on the cluster

        :param url: :class:`string`,
          relative url of the file (given the cluster url)

        :rtype: :class:`requests.Response`
        :returns: the response to the given request

        :raises UnauthorizedException: invalid credentials

        .. note:: additional keyword arguments are passed to the underlying
          :attr:`requests.Session.delete()`
        """
        ret = self._http.delete(self.cluster + url,
                                timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def _put(self, url, **kwargs):
        """performs a PUT on the cluster"""
        ret = self._http.put(self.cluster + url,
                             timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def user_info(self):
        """retrieve information of the current user on the cluster

        :rtype: :class:`QUserInfo`
        :returns: requested information

        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        resp = self._get(get_url('user'))
        resp.raise_for_status()
        ret = resp.json()
        return QUserInfo(ret)

    #move to a better place (session)
    def disks(self):
        """get the list of disks on this cluster for this user

        :rtype: list of :class:`~qapy.disk.QDisk`
        :returns: disks on the cluster owned by the user


        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        response = self._get(get_url('disk folder'))
        if response.status_code != 200:
            response.raise_for_status()
        disks = [QDisk(data, self) for data in response.json()]
        return disks

    def profiles(self):
        """list availables profiles for submitting tasks

        :rtype: list of str
        :returns: list of the profile names

        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        response = self._get(get_url('list profiles'))
        response.raise_for_status()
        if response.status_code != 200:
            return None
        return [QProfile(prof) for prof in response.json()]

    def profile_info(self, profile):
        """get information about a profile

        :param str profile: name of the profile

        :rtype: class:`QProfile`
        :returns: the Qprofile corresponding to requested profile

        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        :raises ValueError: no such profile
        """
        response = self._get(get_url('get profile', name=profile))
        if response.status_code == 404:
            raise ValueError('%s : %s' % (response.json()['message'], profile))
        response.raise_for_status()
        return QProfile(response.json())

    def tasks(self):
        """list tasks stored on this cluster for this user

        :rtype: list of :class:`~qapy.task.QTask`
        :returns: tasks stored on the cluster owned by the user

        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        response = self._get(get_url('tasks'))
        response.raise_for_status()
        ret = []
        for task in response.json():
            task2 = QTask(self, "stub", None, 0)
            task2._update(task)
            ret.append(task2)
        return ret

    def create_disk(self, description, force=False, lock=False):
        """
        create a disk on a cluster

        :param str description: a short description of the disk
        :param bool force: delete an old, unlocked disk
          if maximum number of disks is reached
        :param bool lock: if true prevent the disk to be removed
          by a subsequent :meth:`create_disk` with force set to True

        :rtype: :class:`qapy.disk.QDisk`
        :returns: the created disk

        :raises HTTPError: unhandled http return code
        :raises qapy.connection.UnauthorizedException: invalid credentials
        """
        return QDisk._create(self, description, force, lock)

    def create_task(self, name, profile, frame_nbr):
        """create a new :class:`~qapy.task.QTask`

        :rtype: :class:`~qapy.task.QTask`
        :returns: the created :class:`~qapy.task.QTask`

        :param str name: given name of the task
        :param str profile: which profile to use with this task
        :param int frame_nbr: number of frame on which to run task
        """
        return QTask(self, name, profile, frame_nbr)


###################
# utility Classes #
###################

#would rather use a namedTuple class but no way to document it's fields
class QUserInfo(object):
    """Information about a qapy user"""
    def __init__(self, info):
        self.diskCount = info['diskCount']
        """Number of disks owned by the user"""
        self.maxDisk = info['maxDisk']
        """Maximum number of disks the user is allowed to create"""
        self.taskCount = info['taskCount']
        """Total number of tasks belonging to the user"""
        self.maxTask = info['maxTask']
        """Maximum number of tasks the user is allowed to create"""
        self.runningTaskCount = info['runningTaskCount']
        """Number of tasks currently in 'Submitted' state"""
        self.maxRunningTask = info['maxRunningTask']
        """Maximum number of running tasks the user is allowed to create"""
        self.quotaBytes = info['quotaBytes']
        """total storage space allowed for the user's disks (in Bytes)"""
        self.usedQuotaBytes = info['usedQuotaBytes']
        """total storage space used by the user's disks (in Bytes)"""
        self.maxInstances = info['maxInstances']
        self.executionTime = info['executionTime']

class QProfile(object):
    """information about a profile"""
    def __init__(self,info):
        self.name = info['name'] #: name of the profile
        self.constants = tuple((cst['name'], cst['value'])
                               for cst in info['constants'])
        """list of couples (name, value) representing constants for this profile
        and their default values"""

    def __repr__(self):
        return 'QProfile(name=%s, constants=%r}' % (self.name, self.constants)


##############
# Exceptions #
##############

class UnauthorizedException(Exception):
    """Authorization given is not valid"""
    def __init__(self, auth):
        super(UnauthorizedException, self).__init__(
            "invalid credentials : {}".format(auth))
