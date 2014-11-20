"""Module describing a connection"""

import requests

class QConnection(object):
    def __init__(self, qnode, keyfile):
        self.qnode = qnode
        self.keyfile = keyfile
        self.http = requests.session
        self.http.headers.update({"Authorization": "second"})
        self.http.verify=False #s/False/`file of auth certificates`

    def disks(self): pass

    def profiles(self): pass

    def runningtasks(self): pass
