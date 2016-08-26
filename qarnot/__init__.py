"""Rest API for submitting qarnot jobs in Python."""

__all__ = ["task", "connection", "disk", "notification"]


class QarnotException(Exception):
    """General Connection exception"""
    def __init__(self, msg):
        super(QarnotException, self).__init__("Error : {0}".format(msg))


def raise_on_error(response):
    if response.status_code == 503:
        raise QarnotException("Service Unavailable")
    if response.status_code != 200:
        try:
            raise QarnotException(response.json()['message'])
        except ValueError:
            raise QarnotException(response.text)


def get_url(key, **kwargs):
    """Get and format the url for the given key.
    """
    urls = {
        'disk folder': '/disks',  # GET -> list; POST -> add
        'global disk folder': '/disks/global',  # GET -> list
        'disk force': '/disks/force',  # POST -> force add
        'disk info': '/disks/{name}',  # DELETE -> remove; PUT -> update
        'get disk': '/disks/archive/{name}.{ext}',  # GET-> disk archive
        'tree disk': '/disks/tree/{name}',  # GET -> ls on the disk
        'link disk': '/disks/link/{name}',  # POST -> create links
        'ls disk': '/disks/list/{name}/{path}',  # GET -> ls on the dir {path}
        'update file': '/disks/{name}/{path}',  # POST -> add file; GET -> download file; DELETE -> remove file; PUT -> update file settings
        'tasks': '/tasks',  # GET -> running tasks; POST -> submit task
        'task force': '/tasks/force',  # POST -> force add
        'task update': '/tasks/{uuid}',  # GET->result; DELETE -> abort, PATCH -> update resources
        'task snapshot': '/tasks/{uuid}/snapshot/periodic',  # POST -> snapshots
        'task instant': '/tasks/{uuid}/snapshot',  # POST -> get a snapshot
        'task stdout': '/tasks/{uuid}/stdout',  # GET -> task stdout
        'task stderr': '/tasks/{uuid}/stderr',  # GET -> task stderr
        'task abort': '/tasks/{uuid}/abort',  # GET -> task stderr
        'user': '/info',  # GET -> user info
        'notification': '/notifications',  # GET -> notifications list; POST -> add notification
        'notification update': '/notifications/{uuid}'  # GET -> notification info; DELETE -> remove notification; PUT -> update
    }
    return urls[key].format(**kwargs)

from qarnot.connection import Connection  # noqa

from subprocess import Popen, PIPE  # noqa


def call_git_describe(abbrev=4):
    try:
        p = Popen(['git', 'describe', '--tags', '--dirty', '--always'],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        line = p.stdout.readlines()[0]
        return line.strip()

    except:
        return None


def call_git_rev_parse():
    try:
        p = Popen(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        branch = p.stdout.readlines()[0].strip()

        p = Popen(['git', 'rev-parse', 'HEAD'],
                  stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        sha1 = p.stdout.readlines()[0].strip()

        return branch + "-" + sha1
    except:
        return None


def read_release_version():
    try:
        f = open("RELEASE-VERSION", "r")

        try:
            version = f.readlines()[0]
            return version.strip()

        finally:
            f.close()

    except:
        return None


def write_release_version(version):
    f = open("RELEASE-VERSION", "w")
    f.write("%s\n" % version)
    f.close()


def get_git_version(abbrev=4):
    # Read in the version that's currently in RELEASE-VERSION.
    release_version = read_release_version()

    # version = call_git_describe(abbrev)
    version = call_git_rev_parse()

    # version = pep386adapt(version)

    if version is None:
        version = release_version

    if version is None:
        version = "unknown"

    # If the current version is different from what's in the
    # RELEASE-VERSION file, update the file to be current.

    if version != release_version:
        write_release_version(version)

    return version


def pep386adapt(version):
    # adapt git-describe version to be in line with PEP 386
    parts = version.split('-')
    parts[-2] = 'post'+parts[-2]
    version = '.'.join(parts[:-1])
    return version

__version__ = get_git_version()
