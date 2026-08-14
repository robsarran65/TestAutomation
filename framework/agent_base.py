# =========================================================
# AGENT BASE CLASS - Foundation for all specialized agents
# =========================================================

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
    """Message containing task details"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType = AgentType.TEST_EXECUTOR
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = more urgent
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    created_at: datetime = field(default_factory=datetime.now)
    timeout: int = 300  # seconds
    
    def to_dict(self):
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
    """Result from task execution"""
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
        self.agent_type = agent_type
        self.name = name or agent_type.value
        self.is_running = False
        self.task_queue: List[TaskMessage] = []
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
        """
        Main task handler - wraps execute() with error handling & metrics.
        """
        from datetime import datetime
        
        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.IN_PROGRESS,
        )
        
        try:
            # Check dependencies are met (Coordinator should handle, but defensive)
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id not in self.results:
                        raise Exception(f"Dependency {dep_id} not found")
            
            # Execute the actual task
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
