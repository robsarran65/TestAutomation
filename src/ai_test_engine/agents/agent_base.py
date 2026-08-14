"""
Foundation types for the multi-agent architecture.

Everything the agents pass around is defined here:

    TaskMessage - a unit of work sent *to* an agent
    TaskResult  - what comes back, including status, timing and errors
    Agent       - the abstract base every specialized agent subclasses
    TaskStatus / AgentType - the enums used to route and track work

The flow is: the Coordinator builds a TaskMessage, picks an agent whose
``agent_type`` matches, and calls ``handle_task``. That wrapper runs the
subclass's ``execute`` and guarantees a TaskResult comes back even on failure,
so one crashing agent can never take down a workflow.

To add a new agent: add a member to AgentType, subclass Agent, implement
``execute``, and register an instance with the Coordinator.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
import json
import uuid


class TaskStatus(Enum):
    """Task lifecycle states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    """Agent specialization types"""
    COORDINATOR = "coordinator"
    TEST_EXECUTOR = "test_executor"
    AI_GENERATION = "ai_generation"
    REPORT = "report"
    LOCATOR_REPAIR = "locator_repair"
    DATA_VALIDATOR = "data_validator"
    PERFORMANCE_ANALYZER = "performance_analyzer"


@dataclass
class TaskMessage:
    """One unit of work handed to an agent.

    Attributes:
        task_id: Auto-generated unique id; used to correlate the result and to
            express dependencies between tasks.
        agent_type: Which kind of agent should handle this. The Coordinator
            routes on this field.
        action: The specific operation, e.g. "generate_test_from_description".
            Each agent switches on this inside its ``execute``.
        payload: Arguments for the action. Contents are action-specific.
        priority: Higher runs sooner when several tasks are queued.
        dependencies: task_ids that must complete first. The Coordinator holds
            this task back until all of them have succeeded.
        timeout: Seconds before the task is considered stalled.
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType = AgentType.TEST_EXECUTOR
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more urgent
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    created_at: datetime = field(default_factory=datetime.now)
    timeout: int = 300  # seconds

    def to_dict(self):
        """Return a JSON-safe dict (enums to values, datetimes to ISO strings)."""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type.value,
            "action": self.action,
            "payload": self.payload,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "timeout": self.timeout,
        }


@dataclass
class TaskResult:
    """The outcome of one task.

    Attributes:
        task_id: Matches the originating TaskMessage.
        status: COMPLETED or FAILED. Check this before trusting ``result``.
        result: The agent's output on success; shape is action-specific.
        error: Human-readable failure message when status is FAILED.
        execution_time_ms: Wall-clock duration, filled in by ``handle_task``.
        metadata: Extra diagnostics, e.g. a "traceback" key on failure.
    """
    task_id: str
    agent_type: AgentType
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        """Return a JSON-safe dict (enums to values, datetimes to ISO strings)."""
        return {
            "task_id": self.task_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


class Agent(ABC):
    """
    Base class for all agents.
    
    Agents are specialized workers that:
    - Execute domain-specific tasks
    - Report results to Coordinator
    - Communicate with other agents if needed
    - Handle failures gracefully
    """
    
    def __init__(self, agent_type: AgentType, name: str = ""):
        """Initialize shared agent state.

        Args:
            agent_type: What this agent handles; the Coordinator routes on it.
            name: Human-readable label for logs. Defaults to the type's value.
        """
        self.agent_type = agent_type
        self.name = name or agent_type.value
        self.is_running = False
        self.task_queue: List[TaskMessage] = []
        # Completed results kept by task_id so they can be fetched after the
        # fact (see get_result) rather than only at dispatch time.
        self.results: Dict[str, TaskResult] = {}


    @abstractmethod
    def execute(self, task: TaskMessage) -> TaskResult:
        """
        Execute a single task.
        
        Args:
            task: TaskMessage with action and payload
            
        Returns:
            TaskResult with status, result, and metadata
        """
        pass
    
    def handle_task(self, task: TaskMessage) -> TaskResult:
        """Run a task with error handling and timing. Call this, not execute().

        Wraps the subclass's ``execute`` so that:
          - an exception becomes a FAILED TaskResult instead of propagating
            (one bad agent must not kill the whole workflow), and
          - ``execution_time_ms`` is recorded either way.

        Returns:
            TaskResult: Always a result object, never a raised exception.
        """
        from datetime import datetime


        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.IN_PROGRESS,
        )
        
        try:
            # NOTE: dependencies are deliberately NOT checked here.
            #
            # Dependency resolution belongs to the Coordinator, which holds
            # results for every agent (see CoordinatorAgent._check_dependencies)
            # and only dispatches once they are satisfied. An agent can only
            # see its *own* results, so a defensive re-check here failed every
            # task that depended on work done by a different agent -- i.e.
            # every cross-agent workflow.
            result = self.execute(task)
            
            # Record metrics
            result.end_time = datetime.now()
            result.execution_time_ms = int(
                (result.end_time - result.start_time).total_seconds() * 1000
            )
            
            return result
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
            result.execution_time_ms = int(
                (result.end_time - result.start_time).total_seconds() * 1000
            )
            return result
    
    def log_result(self, result: TaskResult):
        """Store result for retrieval"""
        self.results[result.task_id] = result
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Retrieve stored result"""
        return self.results.get(task_id)
    
    def get_context(self) -> Dict[str, Any]:
        """Return agent state for debugging/monitoring"""
        return {
            "agent_type": self.agent_type.value,
            "name": self.name,
            "is_running": self.is_running,
            "queued_tasks": len(self.task_queue),
            "completed_tasks": len(self.results),
        }
