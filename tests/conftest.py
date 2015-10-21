import pytest
import qapy

@pytest.fixture(scope="module")
def qapy_connection(clean):
    q = qapy.QApy('qarnot.conf')
    if clean:
        for t in q.tasks():
            t.delete()
        for d in q.disks():
            d.delete()
    return q