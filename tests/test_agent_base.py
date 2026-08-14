"""Task lifecycle and error handling in the Agent base class."""

import pytest

from ai_test_engine.agents.agent_base import (
    Agent, AgentType, TaskMessage, TaskResult, TaskStatus,
)


class EchoAgent(Agent):
    """Returns its payload; raises if asked to."""

    def __init__(self):
        super().__init__(AgentType.TEST_EXECUTOR, "Echo")

    def execute(self, task: TaskMessage) -> TaskResult:
        if task.action == "boom":
            raise ValueError("kaboom")
        return TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
            result=task.payload,
        )


def test_handle_task_returns_result_and_records_timing():
    agent = EchoAgent()
    result = agent.handle_task(TaskMessage(action="echo", payload={"a": 1}))

    assert result.status is TaskStatus.COMPLETED
    assert result.result == {"a": 1}
    assert result.end_time is not None
    assert result.execution_time_ms >= 0


def test_handle_task_converts_exception_to_failed_result():
    agent = EchoAgent()
    result = agent.handle_task(TaskMessage(action="boom"))

    assert result.status is TaskStatus.FAILED
    assert "kaboom" in result.error


def test_task_ids_are_unique():
    assert TaskMessage().task_id != TaskMessage().task_id


def test_result_round_trips_to_dict():
    agent = EchoAgent()
    payload = agent.handle_task(TaskMessage(action="echo")).to_dict()

    assert payload["status"] == "completed"
    assert payload["agent_type"] == "test_executor"
    # datetimes must be JSON-safe strings, not datetime objects
    assert isinstance(payload["start_time"], str)


def test_log_and_get_result():
    agent = EchoAgent()
    result = agent.handle_task(TaskMessage(action="echo"))
    agent.log_result(result)

    assert agent.get_result(result.task_id) is result
    assert agent.get_result("nope") is None
