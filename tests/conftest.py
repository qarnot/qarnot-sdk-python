import functools
import os

import pytest
import qapy

MAX_NB_DISKS = 10
BASE_DIR = 'tests'
TMP_DIR =  os.path.join(BASE_DIR, 'tmp')

def exec_x_times(nb_runs):
    def decorator(function):
        def wrapper(*args, **kwargs):
            for i in range(nb_runs):
                function(*args, **kwargs)
        return wrapper
    return decorator


@pytest.fixture(scope="function")
def connection(clean=True):
    q = qapy.QApy('qarnot.conf')
    if clean:
        for t in q.tasks():
            t.delete()
        for d in q.disks():
            d.delete()
    return q


def create_disks(connection, number):
    disks = [connection.create_disk(str(i)) for i in range(number)]
    disks_uuid = [d.uuid for d in disks]
    return disks, disks_uuid


def create_and_add_disks(connection, erd, number):
    disks, disks_uuids = create_disks(connection, number)
    for d_uuid in disks_uuids:
        erd.add_disk(d_uuid)
    return disks, disks_uuids