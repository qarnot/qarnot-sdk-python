import pytest
from functools import reduce
import random

from tests.conftest import qapy_connection, create_disks,\
    create_and_add_disks, exec_x_times, MAX_NB_DISKS
from qapy.task import ExtraResourceDisks

class TestSuite:

    def test_init(self):
        erd = ExtraResourceDisks(None)
        assert len(erd) == 0

    def test_add_non_existing(self):
        erd = ExtraResourceDisks(qapy_connection(clean=True))
        erd.add_disk('1') # Not existing
        assert erd.list_disks() == []
        assert erd.list_uuids() == []
        assert len(erd) == 0

    def test_add_and_list(self):
        connection = qapy_connection(clean=True)
        erd = ExtraResourceDisks(connection)
        nb_disks = random.randrange(1, MAX_NB_DISKS)
        print('testing with {} disks'.format(nb_disks))
        disks, disks_uuids = create_and_add_disks(connection, erd, nb_disks)
        assert reduce(lambda x, y: x and y,
                      [d.uuid in disks_uuids for d in erd.list_disks()])
        assert reduce(lambda x, y: x and y,
                      [d_uuid in disks_uuids for d_uuid in erd.list_uuids()])

    def test_len_and_clean(self):
        connection = qapy_connection(clean=True)
        erd = ExtraResourceDisks(connection)
        nb_disks = random.randrange(1, MAX_NB_DISKS)
        print('testing with {} disks'.format(nb_disks))
        disks, disks_uuids = create_disks(connection, nb_disks)
        assert len(erd) == 0
        for d_uuid in disks_uuids:
            erd.add_disk(d_uuid)
        assert len(erd) == nb_disks
        erd.clean()
        assert erd.list_disks() == []
        assert erd.list_uuids() == []
        assert len(erd) == 0

    def test_empty_after_clean(self):
        erd = ExtraResourceDisks(None)
        erd.clean()
        assert len(erd) == 0

    def test_remove_disk_and_list(self):
        connection = qapy_connection(clean=True)
        erd = ExtraResourceDisks(connection)
        nb_disks = random.randrange(1, MAX_NB_DISKS)
        print('testing with {} disks'.format(nb_disks))
        disks, disks_uuids = create_and_add_disks(connection, erd, nb_disks)
        uuid_del = disks_uuids[nb_disks - 1]
        del disks_uuids[nb_disks - 1]
        erd.remove_disk(uuid_del)
        assert len(erd) == nb_disks - 1
        assert reduce(lambda x, y: x and y,
                      [d.uuid in disks_uuids for d in erd.list_disks()])
        assert reduce(lambda x, y: x and y,
                      [d_uuid in disks_uuids for d_uuid in erd.list_uuids()])

    def test_refresh(self):
        connection = qapy_connection(clean=True)
        erd = ExtraResourceDisks(connection)
        nb_disks = random.randrange(1, MAX_NB_DISKS)
        print('testing with {} disks'.format(nb_disks))
        disks, disks_uuids = create_and_add_disks(connection, erd, nb_disks)
        disks[-1].delete()
        assert len(erd.list_uuids()) == nb_disks
        assert len(erd.list_disks()) == nb_disks - 1
        assert len(erd.list_uuids()) == nb_disks - 1
