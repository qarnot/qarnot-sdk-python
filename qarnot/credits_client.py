from typing import Any, Dict, List

from qarnot import get_url, get_url_with_param, raise_on_error, _util
from qarnot.budget import Budget
from qarnot.exceptions import MissingProjectException, MissingTaskException, MissingPoolException

from requests import Response


class Credits(object):
    """
        Credits details
    """

    def __init__(self, amount_in_euros: float):
        self.amount_in_euros: float = amount_in_euros
        self.amount_in_cents: float = amount_in_euros * 100

    @classmethod
    def from_json(cls, json: Dict[str, Any]):
        """Create a Credits from a json representation

        :param json: the json to use to create the Credits object.
        :type json: `Dict[str, float]`
        :returns: The created :class:`~qarnot.credits_client.Credits`.
        """
        if json is None:
            return None

        credits_in_euro = json.get("credits")
        return Credits(credits_in_euro)


class CreditsClient(object):
    """
        Client used to interact with the Qarnot credits public API.
    """

    def __init__(self, connection):
        """The CreditsClient constructor.

        :param connection: the cluster from where resources are retrieved.
        :type connection: `qarnot.connection.Connection`
        """
        self._connection = connection

    # POOLS
    def _get_pool_credits_raw(self, pool_id: str) -> Response:
        """Requests the credits consumption of the pool `pool_id`.

        :param pool_id: the uuid of the pool
        :type pool_id: `str`
        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.MissingPoolException: Pool was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        response = self._connection._get(get_url('pool credits', uuid=pool_id))
        if response.status_code == 404:
            raise MissingPoolException(_util.get_error_message_from_http_response(response))
        raise_on_error(response)
        return response

    def get_pool_credits(self, pool_id: str) -> Credits:
        """Retrieves the credits consumption of the pool `pool_id` and parses it to a Credits object.

        :param pool_id: the uuid of the pool
        :type pool_id: `str`
        :rtype: Credits
        :raises ~qarnot.exceptions.MissingPoolException: Pool was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        raw_credits = self._get_pool_credits_raw(pool_id)
        return Credits.from_json(raw_credits.json())

    # TASKS
    def _get_task_credits_raw(self, task_id: str) -> Response:
        """Requests the credits consumption of the task `task_id`.

        :param task_id: the uuid of the task
        :type task_id: `str`
        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.MissingTaskException: Task was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        response = self._connection._get(get_url('task credits', uuid=task_id))
        if response.status_code == 404:
            raise MissingTaskException(_util.get_error_message_from_http_response(response))
        raise_on_error(response)
        return response

    def get_task_credits(self, task_id: str) -> Credits:
        """Retrieves the credits consumption of the task `task_id` and parses it to a Credits object.

        :param task_id: the uuid of the task
        :type task_id: `str`
        :rtype: Credits
        :raises ~qarnot.exceptions.MissingTaskException: Task was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        raw_credits = self._get_task_credits_raw(task_id)
        return Credits.from_json(raw_credits.json())

    # ACCOUNTS
    def _get_account_credits_raw(self) -> Response:
        """Requests the credits consumption of the connected account.

        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        response = self._connection._get(get_url('account credits'))
        raise_on_error(response)
        return response

    def get_account_credits(self) -> Credits:
        """Retrieves the credits of the connected account and parses it to a Credits object.

        :rtype: Credits
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        raw_credits = self._get_account_credits_raw()
        return Credits.from_json(raw_credits.json())

    # PROJECT BUDGETS
    def _get_budgets_url(self, uuid: str, only_active: bool):
        return get_url_with_param('project budgets', {'activeOnly': str(only_active)}, uuid=uuid)

    def _get_project_budgets_raw(self, project_id: str, only_active: bool) -> Response:
        """Requests the budgets for the project `project_id`.

        :param project_id: the uuid of the project
        :type project_id: `str`
        :rtype: `requests.Response`
        :raises ~qarnot.exceptions.MissingProjectException: Project was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        response = self._connection._get(self._get_budgets_url(project_id, only_active))
        if response.status_code == 404:
            raise MissingProjectException(_util.get_error_message_from_http_response(response))
        raise_on_error(response)
        return response

    def get_project_budgets(self, project_id: str, only_active: bool) -> List[Budget]:
        """Retrieves the budgets of the project `project_id` and parses it to a list of Budget objects.

        :param project_id: the uuid of the project
        :type project_id: `str`
        :rtype: `List[~qarnot.project.Budget]`
        :raises ~qarnot.exceptions.MissingProjectException: Project was not found.
        :raises ~qarnot.exceptions.UnauthorizedException: Unauthorized.
        :raises ~qarnot.exceptions.QarnotGenericException: API general error, see message for details
        """
        raw_budget = self._get_project_budgets_raw(project_id, only_active)
        budgets_property = raw_budget.json().get("budgets", []) if raw_budget.json() is not None else []
        return [Budget.from_json(budget) for budget in (budgets_property if budgets_property is not None else []) if budget is not None]
