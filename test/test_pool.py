import pytest
import qarnot
from qarnot.pool import Pool
import datetime

class TestPoolProperties:
    class MockConnection:
        def none():
            return

    conn = MockConnection()

    def test_pool_autodelete_default_value(self):
        pool = Pool(self.conn, "pool-name", "profile")
        assert False == pool.auto_delete

    def test_pool_completion_ttl_default_value(self):
        pool = Pool(self.conn, "pool-name", "profile")
        assert "00:00:00" == pool.completion_ttl

    def test_pool_autodelete_set_get(self):
        pool = Pool(self.conn, "pool-name", "profile")
        pool.auto_delete = False
        assert False == pool.auto_delete
        pool.auto_delete = True
        assert True == pool.auto_delete

    def test_pool_completion_ttl_set_get(self):
        pool = Pool(self.conn, "pool-name", "profile")
        pool.completion_ttl = datetime.timedelta(days=2, hours=33, minutes=66, seconds=66)
        assert "3.10:07:06" == pool.completion_ttl
        pool.completion_ttl = "4.11:08:06"
        assert "4.11:08:06" == pool.completion_ttl

    def test_pool_are_in_pool_to_json(self):
        pool = Pool(self.conn, "pool-name", "profile")
        pool.completion_ttl = "4.11:08:06"
        pool.auto_delete = True
        json_pool = pool._to_json()

        assert json_pool['completionTimeToLive'] == '4.11:08:06'
        assert json_pool['autoDeleteOnCompletion'] == True
