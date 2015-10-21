import pytest
from tests.conftest import qapy_connection
from qapy.task import ExtraResourceDisks


class TestSuite:

    def test_init(self):
        erd = ExtraResourceDisks(None)
        assert len(erd) == 0

    def test_add_get(self):
        erd = ExtraResourceDisks(qapy_connection(True))
        erd.add_disk('1') # Not existing
        assert erd.list_disks() == []

    def test_len(self):
        erd = ExtraResourceDisks(qapy_connection(True))
        assert len(erd) == 0
        for i in range(42):
            erd.add_disk(str(i))
        assert len(erd) == 0 # Fixme create real disks

    def test_clean_empty(self):
        erd = ExtraResourceDisks(None)
        erd.clean()
        assert len(erd) == 0

    def test_clean_filled(self):
        erd = ExtraResourceDisks(qapy_connection(True))
        erd.add_disk('1')
        erd.clean()
        assert len(erd) == 0