
from collections.abc import Iterable

import pytest
import qarnot
from qarnot.budget import Budget
from qarnot.project import CreditsClient, Project
from test.mock_project import default_json_all_budgets, json_empty_budgets
from test.mock_connection import MockConnection, MockResponse, GetRequest


class TestBudget:

    def test_get_budgets_of_project(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200, default_json_all_budgets))
        expected_budgets = default_json_all_budgets.get("budgets")
        project = Project("project_id")
        budgets = project.get_all_budgets(conn)


        assert budgets is not None
        assert isinstance(budgets, Iterable)
        assert len(budgets) == 3
        for budget in budgets:
            assert isinstance(budget, Budget)
            assert any(budget._uuid == b["uuid"] for b in expected_budgets)
            expected_budget = next(b for b in expected_budgets if budget._uuid == b["uuid"])
            assert budget._uuid == expected_budget["uuid"]
            assert budget._alias == expected_budget["alias"]
            assert budget._consumed_in_cents == expected_budget["consumedAmountInCents"]
            assert budget._total_in_cents == expected_budget["totalAmountInCents"]
            assert budget._remaining_in_cents == expected_budget["remainingAmountInCents"]
            assert budget._start_date_utc == expected_budget["startDateUtc"]
            assert budget._expiration_date_utc == expected_budget["expirationDateUtc"]
            assert budget._budget_overrun_policy == expected_budget["budgetOverrunPolicy"]
            assert budget._is_archived == expected_budget["isArchived"]

    def test_get_empty_list_of_budgets(self):
        conn = MockConnection()
        conn.add_response(MockResponse(200, json_empty_budgets))
        project = Project("project_id")
        budgets = project.get_all_budgets(conn)

        assert budgets is not None
        assert isinstance(budgets, Iterable)
        assert len(budgets) == 0

    def test_get_budgets_of_non_existing_project(self):
        conn = MockConnection()
        conn.add_response(MockResponse(404,{"message": "Project not found"}))
        budget_client = CreditsClient(conn)
        with pytest.raises(qarnot.exceptions.MissingProjectException):
            _ = budget_client.get_project_budgets("unknown_project_id", True)

    def test_get_budgets_activeOnly_parameter(self):
        conn = MockConnection()
        project = Project("project_id")

        budgets = project.get_all_budgets(conn)
        assert conn.requests[0].uri == qarnot.get_url('project budgets', uuid='project_id') + "?activeOnly=False"

        budgets = project.get_active_budgets(conn)
        assert conn.requests[1].uri == qarnot.get_url('project budgets', uuid='project_id') + "?activeOnly=True"

