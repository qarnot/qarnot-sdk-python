
import pytest
import qarnot
from qarnot.credits_client import CreditsClient, Credits
from test.mock_credits import default_json_credits
from test.mock_connection import MockConnection, MockResponse, GetRequest


class TestCredits:

    def test_get_credits_of_pool(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200, default_json_credits))
        credits_client = CreditsClient(conn)
        credits = credits_client.get_pool_credits("pool_id")

        assert credits is not None
        assert isinstance(credits, Credits)
        assert credits.amount_in_euros == 3600.42
        assert credits.amount_in_cents == 360042

    def test_get_credits_of_non_existing_pool(self):
        conn = MockConnection()
        conn.add_response(MockResponse(404,{"message": "Pool not found"}))
        credits_client = CreditsClient(conn)
        with pytest.raises(qarnot.exceptions.MissingPoolException):
            _ = credits_client.get_pool_credits("pool_id")

    def test_get_credits_of_task(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200, default_json_credits))
        credits_client = CreditsClient(conn)
        credits = credits_client.get_task_credits("task_id")

        assert credits is not None
        assert isinstance(credits, Credits)
        assert credits.amount_in_euros == 3600.42
        assert credits.amount_in_cents == 360042

    def test_get_credits_of_non_existing_task(self):
        conn = MockConnection()
        conn.add_response(MockResponse(404,{"message": "Task not found"}))
        credits_client = CreditsClient(conn)
        with pytest.raises(qarnot.exceptions.MissingTaskException):
            _ = credits_client.get_task_credits("task_id")

    def test_get_credits_of_account(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200, default_json_credits))
        credits_client = CreditsClient(conn)

        credits = credits_client.get_account_credits()
        assert isinstance(credits, Credits)
        assert credits.amount_in_euros == 3600.42
        assert credits.amount_in_cents == 360042

