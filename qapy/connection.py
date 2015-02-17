"""Module describing a connection."""

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
    """Represents the couple cluster/user to which submit tasks.

    .. automethod:: __init__
    """
    def __init__(self, conf):
        """Create a connection to a cluster with given config file or
        dictionary.

        :param conf: path to a qarnot configuration file or dictionary
          containing following keys:
        * cluster_url
        * cluster_unsafe   (optional)
        * cluster_timeout  (optional)
        * client_auth
        .. note:: qarnot.conf file format:
        ::

           [cluster]
           # url of the REST API
           url=https://localhost
           # No SSL verification ?
           unsafe=False
           # timeout put on every GET/POST
           timeout=30
           [client]
           # auth string of the client
           auth=login
        """
        self._http = requests.session()

        if isinstance(conf, dict):
            self.cluster = conf['cluster_url']
            self._http.headers.update({"Authorization": conf['client_auth']})
            self.auth = conf['client_auth']
            self.timeout = conf.get('cluster_timeout')
            if conf.get('cluster_unsafe'):
                self._http.verify = False
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

                if cfg.has_option('cluster', 'unsafe') \
                   and cfg.getboolean('cluster', 'unsafe'):
                    self._http.verify = False

    def _get(self, url, **kwargs):
        """Perform a GET request on the cluster.

        :param str url:
          relative url of the file (according to the cluster url)

        :rtype: :class:`requests.Response`
        :returns: The response to the given request.

        :raises UnauthorizedException: invalid credentials

        .. note:: Additional keyword arguments are passed to the underlying
           :func:`requests.Session.get`.
        """
        ret = self._http.get(self.cluster + url, timeout=self.timeout,
                             **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def _post(self, url, json=None, **kwargs):
        """perform a POST request on the cluster

        :param url: :class:`string`,
          relative url of the file (according to the cluster url)
        :param json: the data to json serialize and post

        :rtype: :class:`requests.Response`
        :returns: The response to the given request.

        :raises UnauthorizedException: invalid credentials

        .. note:: Additional keyword arguments are passed to the underlying
           :attr:`requests.Session.post()`.
        """
        ret = self._http.post(self.cluster + url, json=json,
                              timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret


    def _delete(self, url, **kwargs):
        """Perform a DELETE request on the cluster.

        :param url: :class:`string`,
          relative url of the file (according to the cluster url)

        :rtype: :class:`requests.Response`
        :returns: The response to the given request.

        :raises UnauthorizedException: invalid credentials

        .. note:: Additional keyword arguments are passed to the underlying
          :attr:`requests.Session.delete()`.
        """
        ret = self._http.delete(self.cluster + url,
                                timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def _put(self, url, **kwargs):
        """Performs a PUT on the cluster."""
        ret = self._http.put(self.cluster + url,
                             timeout=self.timeout, **kwargs)
        if ret.status_code == 401:
            raise UnauthorizedException(self.auth)
        return ret

    def user_info(self):
        """Get informations of the current user on the cluster.

        :rtype: :class:`QUserInfo`
        :returns: Requested informations.

        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        resp = self._get(get_url('user'))
        resp.raise_for_status()
        ret = resp.json()
        return QUserInfo(ret)

    #move to a better place (session)
    def disks(self):
        """Get the list of disks on this cluster for this user.

        :rtype: List of :class:`~qapy.disk.QDisk`.
        :returns: Disks on the cluster owned by the user.


        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        response = self._get(get_url('disk folder'))
        if response.status_code != 200:
            response.raise_for_status()
        disks = [QDisk(data, self) for data in response.json()]
        return disks

    def profiles(self):
        """Get the list of available profiles for submitting tasks.

        :rtype: List of :class:`str`.
        :returns: List of the names of profiles.

        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        response = self._get(get_url('list profiles'))
        response.raise_for_status()
        if response.status_code != 200:
            return None
        return [QProfile(prof) for prof in response.json()]

    def profile_info(self, profile):
        """Get informations about a profile.

        :param str profile: name of the profile

        :rtype: :class:`QProfile`
        :returns: The :class:`QProfile` corresponding to the requested profile.

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
        """Get the list of tasks stored on this cluster for this user.

        :rtype: List of :class:`~qapy.task.QTask`.
        :returns: Tasks stored on the cluster owned by the user.

        :raises qapy.connection.UnauthorizedException: invalid credentials
        :raises HTTPError: unhandled http return code
        """
        response = self._get(get_url('tasks'))
        response.raise_for_status()
        ret = []
        for task in response.json():
            task2 = QTask(self, "stub", None, 0, False)
            task2._update(task)
            ret.append(task2)
        return ret

    def create_task(self, name, profile, frame_nbr, force=False):
        """Create a new :class:`~qapy.task.QTask`.

        :param str name: given name of the task
        :param str profile: which profile to use with this task
        :param int frame_nbr: number of frame on which to run task
        :param bool force: remove an old task if the maximum number of allowed
           tasks is reached. Plus, it will delete an old unlocked disk
           if maximum number of disks is reached for resources and results

        :rtype: :class:`~qapy.task.QTask`
        :returns: The created :class:`~qapy.task.QTask`.

        .. note:: See available profiles with :meth:`profiles`.
        """
        return QTask(self, name, profile, frame_nbr, force)


###################
# utility Classes #
###################

#would rather use a namedTuple class but no way to document it's fields
class QUserInfo(object):
    """Informations about a qapy user."""
    def __init__(self, info):
        self.diskCount = info['diskCount']
        """:type: :class:`int`

        Number of disks owned by the user."""
        self.maxDisk = info['maxDisk']
        """:type: :class:`int`

        Maximum number of disks allowed (resource and result disks)."""
        self.quotaBytes = info['quotaBytes']
        """:type: :class:`int`

        Total storage space allowed for the user's disks (in Bytes)."""
        self.usedQuotaBytes = info['usedQuotaBytes']
        """:type: :class:`int`

        Total storage space used by the user's disks (in Bytes)."""
        self.taskCount = info['taskCount']
        """:type: :class:`int`

        Total number of tasks belonging to the user."""
        self.maxTask = info['maxTask']
        """:type: :class:`int`

        Maximum number of tasks the user is allowed to create."""
        self.runningTaskCount = info['runningTaskCount']
        """:type: :class:`int`

        Number of tasks currently in 'Submitted' state."""
        self.maxRunningTask = info['maxRunningTask']
        """:type: :class:`int`

        Maximum number of tasks in 'Submitted' state."""
        self.maxInstances = info['maxInstances']
        """:type: :class:`int`

        Maximum number of frames per task."""
        self.executionTime = info['executionTime']
        """:type: :class:`int`

        Total computation time."""

class QProfile(object):
    """Informations about a profile."""
    def __init__(self,info):
        self.name = info['name']
        """:type: :class:`str`

        Name of the profile."""
        self.constants = tuple((cst['name'], cst['value'])
                               for cst in info['constants'])
        """:type: List of (:class:`str`, :class:`str`)

        List of couples (name, value) representing constants for this profile
        and their default values."""

    def __repr__(self):
        return 'QProfile(name=%s, constants=%r}' % (self.name, self.constants)


##############
# Exceptions #
##############

class UnauthorizedException(Exception):
    """Authorization given is not valid."""
    def __init__(self, auth):
        super(UnauthorizedException, self).__init__(
            "invalid credentials : {}".format(auth))
