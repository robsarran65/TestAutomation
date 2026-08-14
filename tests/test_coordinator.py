"""Coordinator routing, result aggregation, and status reporting."""

from ai_test_engine.agents.agent_base import (
    Agent, AgentType, TaskMessage, TaskResult, TaskStatus,
)
from ai_test_engine.agents.coordinator import CoordinatorAgent


class StubAgent(Agent):
    def __init__(self, agent_type=AgentType.AI_GENERATION):
        super().__init__(agent_type, "Stub")
        self.seen = []

    def execute(self, task: TaskMessage) -> TaskResult:
        self.seen.append(task.action)
        return TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
            result={"ok": True},
        )


def test_register_and_look_up_agent():
    coord, agent = CoordinatorAgent(), StubAgent()
    agent_id = coord.register_agent(agent)

    assert agent_id.startswith("ai_generation")
    assert coord.get_available_agent(AgentType.AI_GENERATION) is agent
    assert coord.get_available_agent(AgentType.REPORT) is None


def test_dispatch_routes_to_agent_and_stores_result():
    coord, agent = CoordinatorAgent(), StubAgent()
    coord.register_agent(agent)

    task = TaskMessage(agent_type=AgentType.AI_GENERATION, action="generate")
    coord.submit_task(task)
    coord._dispatch_task(task)

    assert agent.seen == ["generate"]
    assert coord.task_results[task.task_id].status is TaskStatus.COMPLETED
    assert coord.get_task_status(task.task_id)["status"] == "completed"


def test_workflow_chains_dependencies_in_order():
    coord = CoordinatorAgent()
    tasks = [
        TaskMessage(agent_type=AgentType.AI_GENERATION, action=f"step{i}")
        for i in range(3)
    ]
    coord.submit_workflow("wf-1", tasks)

    assert tasks[0].dependencies == []
    assert tasks[1].dependencies == [tasks[0].task_id]
    assert tasks[2].dependencies == [tasks[1].task_id]
    assert coord.get_workflow_status("wf-1")["total_tasks"] == 3


def test_dependencies_gate_until_prerequisite_completes():
    coord, agent = CoordinatorAgent(), StubAgent()
    coord.register_agent(agent)

    first = TaskMessage(agent_type=AgentType.AI_GENERATION, action="first")
    second = TaskMessage(
        agent_type=AgentType.AI_GENERATION, action="second",
        dependencies=[first.task_id],
    )

    assert coord._check_dependencies(second) is False
    coord.submit_task(first)
    coord._dispatch_task(first)
    assert coord._check_dependencies(second) is True


def test_system_status_counts_completions():
    coord, agent = CoordinatorAgent(), StubAgent()
    coord.register_agent(agent)
    task = TaskMessage(agent_type=AgentType.AI_GENERATION, action="go")
    coord.submit_task(task)
    coord._dispatch_task(task)

    status = coord.get_system_status()
    assert status["total_tasks"] == 1
    assert status["completed_tasks"] == 1
    assert status["failed_tasks"] == 0


def test_coordinator_refuses_to_execute_tasks_itself():
    result = CoordinatorAgent().execute(TaskMessage(action="anything"))
    assert result.status is TaskStatus.FAILED


def test_cross_agent_dependency_does_not_fail_the_task():
    """Regression: a task depending on ANOTHER agent's task must still run.

    handle_task used to re-check dependencies against the agent's own results
    dict. An agent never holds another agent's results, so every cross-agent
    dependency failed instantly -- which silently broke the entire
    multi-agent workflow.
    """
    coord = CoordinatorAgent()
    generator = StubAgent(AgentType.AI_GENERATION)
    executor = StubAgent(AgentType.TEST_EXECUTOR)
    coord.register_agent(generator)
    coord.register_agent(executor)

    first = TaskMessage(agent_type=AgentType.AI_GENERATION, action="generate")
    coord.submit_task(first)
    coord._dispatch_task(first)

    # second is handled by a DIFFERENT agent than the one that ran `first`
    second = TaskMessage(
        agent_type=AgentType.TEST_EXECUTOR,
        action="execute",
        dependencies=[first.task_id],
    )
    coord.submit_task(second)
    assert coord._check_dependencies(second) is True   # coordinator is satisfied
    coord._dispatch_task(second)

    result = coord.task_results[second.task_id]
    assert result.status is TaskStatus.COMPLETED, f"regressed: {result.error}"
    assert executor.seen == ["execute"]


def test_agent_runs_dependent_task_it_never_saw_the_dependency_for():
    """The agent itself must not second-guess the Coordinator."""
    agent = StubAgent()
    result = agent.handle_task(
        TaskMessage(action="go", dependencies=["some-other-agents-task-id"])
    )

    assert result.status is TaskStatus.COMPLETED


def test_unknown_ids_return_none():
    coord = CoordinatorAgent()
    assert coord.get_task_status("missing") is None
    assert coord.get_workflow_status("missing") is None
