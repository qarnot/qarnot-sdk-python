from .mock_connection import MockResponse
from qarnot._retry import with_retry

class MockConnection:
    def __init__(self, responses):
        self._retry_count = 2
        self._retry_wait = 0

        self.calls = 0
        self._responses = responses

    @with_retry
    def get(self, *args, **kwargs):
        self.calls += 1

        if len(self._responses) > 0:
            resp = self._responses[0]
            self._responses = self._responses[1:]
            return resp

        return MockResponse(200)


class TestRetry:
    def test_failing_all_the_way(self):
        conn = MockConnection(
            [MockResponse(429)] * 4
        )
        resp = conn.get()
        assert resp.status_code == 429
        assert conn.calls == 3

    def test_eventually_succeeding(self):
        conn = MockConnection(
                [MockResponse(429)] * 2 + [MockResponse(200, json={"message": "hello"})]
        )
        resp = conn.get()
        assert resp.status_code == 200
        json = resp.json()
        assert "message" in json
        assert json["message"] == "hello"
        assert conn.calls == 3
