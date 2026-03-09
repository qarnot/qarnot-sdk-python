"""Module to handle task dependencies."""

# Copyright 2017 Qarnot computing
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, List, Optional


class TaskFinalState(object):
    """Represents a required final state for an advanced dependency condition.

    Use the concrete subclasses:
    :class:`TaskFinalStateSuccess`, :class:`TaskFinalStateFailure`,
    :class:`TaskFinalStateCancelled`.
    """

    value: str = ""

    @classmethod
    def from_string(cls, value: str) -> "TaskFinalState":
        """Create a :class:`TaskFinalState` from a string.

        :param value: one of ``"success"``, ``"failure"``, ``"cancelled"``
            (case-insensitive).
        :type value: :class:`str`
        :returns: The matching :class:`TaskFinalState` instance.
        :raises ValueError: if the value is not recognised.
        """
        if value is None:
            return None
        lower = value.lower()
        if lower == TaskFinalStateSuccess.value:
            return TaskFinalStateSuccess()
        elif lower == TaskFinalStateFailure.value:
            return TaskFinalStateFailure()
        elif lower == TaskFinalStateCancelled.value:
            return TaskFinalStateCancelled()
        else:
            return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TaskFinalState):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __lt__(self, other: "TaskFinalState") -> bool:
        return self.value < other.value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return "TaskFinalState({})".format(self.value)


class TaskFinalStateSuccess(TaskFinalState):
    """Task final state: the dependency task completed successfully."""

    value: str = "success"

    def __init__(self):
        pass


class TaskFinalStateFailure(TaskFinalState):
    """Task final state: the dependency task failed."""

    value: str = "failure"

    def __init__(self):
        pass


class TaskFinalStateCancelled(TaskFinalState):
    """Task final state: the dependency task was cancelled."""

    value: str = "cancelled"

    def __init__(self):
        pass


class DependencyState(object):
    """Represents the resolution state of a dependency as reported by the API.

    Use the concrete subclasses:
    :class:`DependencyStateWaiting`,
    :class:`DependencyStateConditionsFulfilled`,
    :class:`DependencyStateConditionsNotFulfilled`.
    """

    value: str = ""

    @classmethod
    def from_string(cls, value: str) -> Optional["DependencyState"]:
        """Create a :class:`DependencyState` from a string.

        :param value: one of ``"waiting"``, ``"dependencyConditionsFulfilled"``,
            ``"dependencyConditionsNotFulfilled"`` (case-insensitive).
        :type value: :class:`str`
        :returns: The matching :class:`DependencyState` instance, or None if value is None.
        """
        if value is None:
            return None
        lower = value.lower()
        if lower == DependencyStateWaiting.value.lower():
            return DependencyStateWaiting()
        elif lower == DependencyStateConditionsFulfilled.value.lower():
            return DependencyStateConditionsFulfilled()
        elif lower == DependencyStateConditionsNotFulfilled.value.lower():
            return DependencyStateConditionsNotFulfilled()
        else:
            return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DependencyState):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return "DependencyState({})".format(self.value)


class DependencyStateWaiting(DependencyState):
    """Dependency state: waiting for the dependency task to reach its final state."""

    value: str = "waiting"

    def __init__(self):
        pass


class DependencyStateConditionsFulfilled(DependencyState):
    """Dependency state: the dependency conditions have been fulfilled."""

    value: str = "dependencyConditionsFulfilled"

    def __init__(self):
        pass


class DependencyStateConditionsNotFulfilled(DependencyState):
    """Dependency state: the dependency conditions have not been fulfilled."""

    value: str = "dependencyConditionsNotFulfilled"

    def __init__(self):
        pass


class AdvancedDependency(object):
    """An advanced dependency on another task with optional final-state conditions.

    Used as input to :meth:`~qarnot.task.Task.set_task_advanced_dependencies`.

    :param task_uuid: the UUID of the task this dependency refers to.
    :type task_uuid: :class:`str`
    :param task_final_state_condition: required final states for this dependency to be
        considered fulfilled. ``None`` or an empty list means any final state is accepted.
    :type task_final_state_condition: list of :class:`TaskFinalState` or None
    """

    def __init__(
        self,
        task_uuid: str,
        task_final_state_condition: Optional[List[TaskFinalState]] = None
    ):
        """Create an advanced dependency.

        :param task_uuid: UUID of the dependency task.
        :type task_uuid: :class:`str`
        :param task_final_state_condition: required final states.
            Valid values are :class:`TaskFinalStateSuccess`,
            :class:`TaskFinalStateFailure`, :class:`TaskFinalStateCancelled`.
            ``None`` or ``[]`` means any final state.
        :type task_final_state_condition: list of :class:`TaskFinalState` or None
        """
        self._task_uuid: str = task_uuid
        if task_final_state_condition:
            # Why sorted? So that lists comparison will work properly
            self._task_final_state_condition: Optional[List[TaskFinalState]] = sorted(
                task_final_state_condition)
        else:
            self._task_final_state_condition = None

    @property
    def task_uuid(self) -> str:
        """:type: :class:`str`
        :getter: Returns the UUID of the dependency task.
        """
        return self._task_uuid

    @property
    def task_final_state_condition(self) -> Optional[List[TaskFinalState]]:
        """:type: list of :class:`TaskFinalState` or None
        :getter: Returns the required final states, or None for any final state.
        """
        return self._task_final_state_condition

    def to_json(self) -> Dict[str, Any]:
        """Get a dict ready to be json packed.

        :return: the json representation of this advanced dependency.
        :rtype: :class:`dict`
        """
        return {
            "taskUuid": self._task_uuid,
            "taskFinalStateCondition": (
                [s.value for s in self._task_final_state_condition]
                if self._task_final_state_condition is not None else None
            ),
        }

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "AdvancedDependency":
        """Create an :class:`AdvancedDependency` from a json dict.

        :param json: dictionary representing the advanced dependency.
        :type json: :class:`dict`
        :returns: The created :class:`~qarnot.dependency.AdvancedDependency`.
        """
        raw_conditions = json.get("taskFinalStateCondition")
        conditions = (
            [TaskFinalState.from_string(s) for s in raw_conditions]
            if raw_conditions else None
        )
        return cls(
            task_uuid=json.get("taskUuid"),
            task_final_state_condition=conditions,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AdvancedDependency):
            return False
        return (self._task_uuid == other._task_uuid
                and self._task_final_state_condition == other._task_final_state_condition)

    def __str__(self) -> str:
        return "AdvancedDependency on task '{}' with conditions {}.".format(
            self._task_uuid, self._task_final_state_condition)

    def __repr__(self) -> str:
        return "AdvancedDependency(task_uuid={}, task_final_state_condition={})".format(
            self._task_uuid, self._task_final_state_condition)


class AdvancedDependencyOutput(object):
    """An advanced dependency as returned by the API, including its resolution state.

    .. note:: Read-only class — populated from API responses.
    """

    def __init__(
        self,
        task_uuid: str,
        task_final_state_condition: Optional[List[TaskFinalState]],
        state: Optional[DependencyState],
        actual_final_state: Optional[TaskFinalState] = None
    ):
        self._task_uuid: str = task_uuid
        self._task_final_state_condition: Optional[List[TaskFinalState]] = task_final_state_condition
        self._state: Optional[DependencyState] = state
        self._actual_final_state: Optional[TaskFinalState] = actual_final_state

    @property
    def task_uuid(self) -> str:
        """:type: :class:`str`
        :getter: Returns the UUID of the dependency task.
        """
        return self._task_uuid

    @property
    def task_final_state_condition(self) -> Optional[List[TaskFinalState]]:
        """:type: list of :class:`TaskFinalState` or None
        :getter: Returns the required final states, or None for any final state.
        """
        return self._task_final_state_condition

    @property
    def state(self) -> Optional[DependencyState]:
        """:type: :class:`DependencyState` or None
        :getter: Returns the resolution state of this dependency.
        """
        return self._state

    @property
    def actual_final_state(self) -> Optional[TaskFinalState]:
        """:type: :class:`TaskFinalState` or None
        :getter: Returns the actual final state of the dependency task, or None if not yet final.
        """
        return self._actual_final_state

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "AdvancedDependencyOutput":
        """Create an :class:`AdvancedDependencyOutput` from a json dict.

        :param json: dictionary representing the advanced dependency output.
        :type json: :class:`dict`
        :returns: The created :class:`~qarnot.dependency.AdvancedDependencyOutput`.
        """
        raw_conditions = json.get("taskFinalStateCondition")
        conditions = (
            [TaskFinalState.from_string(s) for s in raw_conditions]
            if raw_conditions else None
        )
        raw_actual = json.get("actualFinalState")
        return cls(
            task_uuid=json.get("taskUuid"),
            task_final_state_condition=conditions,
            state=DependencyState.from_string(json.get("state")),
            actual_final_state=TaskFinalState.from_string(raw_actual)
        )

    def __str__(self) -> str:
        return "AdvancedDependencyOutput on task '{}' (state: {}).".format(
            self._task_uuid, self._state)

    def __repr__(self) -> str:
        return "AdvancedDependencyOutput(task_uuid={}, state={})".format(
            self._task_uuid, self._state)


class TaskDependencies(object):
    """Read-only view of a task's dependencies and their resolution state.

    Populated from the API's ``DependencyOutput`` response after task submission.

    For tasks with simple dependencies: :attr:`depends_on` is populated,
    :attr:`advanced_depends_on` is empty.

    For tasks with advanced dependencies: :attr:`advanced_depends_on` is populated.

    .. note:: Read-only class — populated from API responses.
    """

    def __init__(
        self,
        depends_on: Optional[List[str]] = None,
        advanced_depends_on: Optional[List[AdvancedDependencyOutput]] = None,
        state: Optional[DependencyState] = None,
    ):
        self._depends_on: List[str] = depends_on or []
        self._advanced_depends_on: List[AdvancedDependencyOutput] = advanced_depends_on or []
        self._state: Optional[DependencyState] = state

    @property
    def depends_on(self) -> List[str]:
        """:type: list of :class:`str`
        :getter: Returns the simple dependency task UUIDs.
        """
        return self._depends_on

    @property
    def advanced_depends_on(self) -> List[AdvancedDependencyOutput]:
        """:type: list of :class:`~qarnot.dependency.AdvancedDependencyOutput`
        :getter: Returns the advanced dependencies with per-dependency state.
        """
        return self._advanced_depends_on

    @property
    def state(self) -> Optional[DependencyState]:
        """:type: :class:`DependencyState` or None
        :getter: Returns the overall dependency resolution state,
            or None if not yet resolved.
        """
        return self._state

    @classmethod
    def from_json(cls, json: Optional[Dict[str, Any]]) -> Optional["TaskDependencies"]:
        """Parse the ``dependencies`` block from a task API response.

        :param json: the ``dependencies`` dict from the API, or None.
        :type json: :class:`dict` or None
        :returns: The created :class:`~qarnot.dependency.TaskDependencies`, or None if json is None.
        """
        if json is None:
            return None
        depends_on = json.get("dependsOn") or []
        adv_json = json.get("advancedDependsOn")
        advanced = [AdvancedDependencyOutput.from_json(x) for x in adv_json] if adv_json else []
        state = DependencyState.from_string(json.get("state"))
        return cls(depends_on, advanced, state)

    def __str__(self) -> str:
        return "TaskDependencies(state={}, depends_on={}, advanced_depends_on={})".format(
            self._state, self._depends_on, self._advanced_depends_on)

    def __repr__(self) -> str:
        return "TaskDependencies(state={}, depends_on={}, advanced_depends_on={})".format(
            self._state, self._depends_on, self._advanced_depends_on)
