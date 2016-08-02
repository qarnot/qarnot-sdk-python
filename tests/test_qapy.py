import pytest
import sys

import qarnot
from qarnot.connection import UnauthorizedException

if sys.version_info[0] >= 3:  # module renamed in py3
    import configparser as config  # pylint: disable=import-error
else:
    import ConfigParser as config  # pylint: disable=import-error



class TestSuite:
    def test_dict_auth(self):
        cfg = config.ConfigParser()
        conf = {}
        with open('qarnot.conf') as cfgfile:
            cfg.readfp(cfgfile)
            conf['cluster_url'] = cfg.get('cluster', 'url')
            conf['client_auth'] = cfg.get('client', 'auth')
            if cfg.has_option('cluster', 'timeout'):
                conf['cluster_timeout'] = cfg.getint('cluster', 'timeout')
            else:
                conf['cluster_timeout'] = 3000
            if cfg.has_option('cluster', 'unsafe') \
               and cfg.getboolean('cluster', 'unsafe'):
                conf['cluster_unsafe'] = True
            else:
                conf['cluster_unsafe'] = False
        q = qarnot.QApy(conf)
        q.tasks()

    def test_bad_auths(self):
        cfg = config.ConfigParser()
        conf = {}
        with open('qarnot.conf') as cfgfile:
            cfg.readfp(cfgfile)
            conf['cluster_url'] = cfg.get('cluster', 'url')
            if cfg.has_option('cluster', 'timeout'):
                conf['cluster_timeout'] = cfg.getint('cluster', 'timeout')
            else:
                conf['cluster_timeout'] = 3000
            if cfg.has_option('cluster', 'unsafe') \
               and cfg.getboolean('cluster', 'unsafe'):
                conf['cluster_unsafe'] = True
            else:
                conf['cluster_unsafe'] = False
        conf['client_auth'] = 'non-existing-user-auth'
        with pytest.raises(UnauthorizedException):
            q = qarnot.QApy(conf)
            q.tasks()