from datetime import datetime


class BudgetOverrunPolicy():
    """Represents the policy that will act on project compute if the budget is exceeded."""
    policy: str = None

    @classmethod
    def from_string(cls, policy: str):
        """Create a budget overrun policy from string.

        :returns: The created :class:`~qarnot.project.BudgetOverrunPolicy`.
        """

        if policy is None:
            return None

        if policy.lower() == AlertOnlyPolicy.policy.lower():
            return AlertOnlyPolicy()
        elif policy.lower() == BlockNewPolicy.policy.lower():
            return BlockNewPolicy()
        elif policy.lower() == StopAndBlockAllPolicy.policy.lower():
            return StopAndBlockAllPolicy()
        else:
            return None

    def __str__(self) -> str:
        return "budget overrun policy {}.".format(self.policy)

    def __repr__(self) -> str:
        return str(self.policy)


class Budget(object):
    """Represents a project budget.

    .. note::
       A :class:`Budget` must be retrieved with :attr:`qarnot.connection.Connection.user_info.projects`.
    """
    def __init__(self, uuid: str, alias: str, consumed_in_cents: int, total_in_cents: int, remaining_in_cents: int,
                 budget_overrun_policy: BudgetOverrunPolicy, start_date_utc: datetime, expiration_date_utc: datetime, is_archived: bool):
        """Create a new :class:`Budget`.

        :param str uuid: Unique identifier of the budget.
        :param alias: Human-readable label for the budget. Empty string if none was set.
        :type alias: :class:`str` or None
        :param int consumed_in_cents: Amount already consumed, in euro cents.
        :param int total_in_cents: Total budget cap, in euro cents.
        :param int remaining_in_cents: Remaining amount before the cap is hit, in euro cents.
        :param budget_overrun_policy: Policy applied when consumption reaches the budget cap.
            One of: :class:`~qarnot.project.AlertOnlyPolicy`, :class:`~qarnot.project.BlockNewPolicy`,
            :class:`~qarnot.project.StopAndBlockAllPolicy`. None means the project's default policy applies.
        :type budget_overrun_policy: :class:`~qarnot.project.BudgetOverrunPolicy` or None
        :param datetime start_date_utc: Date from which the budget starts being consumed (UTC).
        :param expiration_date_utc: Date after which the budget is no longer active (UTC).
            None means no expiration.
        :type expiration_date_utc: :class:`datetime.datetime` or None
        :param bool is_archived: Whether the budget has been archived.
            Archived budgets are no longer consumed.
        """
        self._alias: str = alias
        self._uuid: str = uuid
        self._consumed_in_cents: int = consumed_in_cents
        self._total_in_cents: int = total_in_cents
        self._remaining_in_cents: int = remaining_in_cents
        self._budget_overrun_policy: BudgetOverrunPolicy = budget_overrun_policy
        self._start_date_utc: datetime = start_date_utc
        self._expiration_date_utc: datetime = expiration_date_utc
        self._is_archived: bool = is_archived

    @classmethod
    def from_json(cls, json_budget) -> "Budget":
        """Create a Budget object from a json budget.

        :param qarnot.connection.Connection connection: the cluster connection
        :param dict json_budget: Dictionary representing the budget
        :returns: The created :class:`~qarnot.project.Budget`.
        """
        if json_budget is None:
            return None

        project = cls(
            json_budget.get("uuid"),
            json_budget.get("alias"),
            json_budget.get("consumedAmountInCents"),
            json_budget.get("totalAmountInCents"),
            json_budget.get("remainingAmountInCents"),
            json_budget.get("budgetOverrunPolicy"),
            json_budget.get("startDateUtc"),
            json_budget.get("expirationDateUtc"),
            json_budget.get("isArchived"))

        return project


class AlertOnlyPolicy(BudgetOverrunPolicy):
    """Represents a 'alert only' policy: no action on the running and future compute"""
    policy: str = "AlertOnly"

    def __init__(self):
        """ Create a new 'alert only' policy."""


class BlockNewPolicy(BudgetOverrunPolicy):
    """Represents 'block new' policy: all new compute will failed to be created but running compute will continue"""
    policy: str = "BlockNew"

    def __init__(self):
        """ Create a new 'block new' policy."""


class StopAndBlockAllPolicy(BudgetOverrunPolicy):
    """Represents a 'stop and block all' policy: all new and running compute will fail immediatly' """
    policy: str = "StopAndBlockAll"

    def __init__(self):
        """ Create a new 'stop and block all' policy."""
