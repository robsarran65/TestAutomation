"""
The Coordinator: the orchestrator every other agent reports to.

Nothing calls the specialized agents directly. Work is submitted here, and the
Coordinator decides who runs it and when:

    1. Agents register themselves (``register_agent``) declaring their type.
    2. A caller submits a TaskMessage (``submit_task``) or an ordered chain of
       them (``submit_workflow``).
    3. Tasks queue by priority. A task whose ``dependencies`` haven't finished
       is put back on the queue rather than run early.
    4. ``_dispatch_task`` finds a matching agent, runs the task, stores the
       result, and retries on failure up to ``max_retries``.

Results are kept indexed by task_id and aggregated per workflow, so a caller
can poll ``get_task_status`` / ``get_workflow_status`` at any point.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict
import threading
import time
from queue import Empty, PriorityQueue
import json

from ai_test_engine.agents.agent_base import (
    Agent, AgentType, TaskMessage, TaskResult, TaskStatus
)


class CoordinatorAgent(Agent):
    """
    Central coordinator that:
    - Receives tasks from UI/API
    - Routes to appropriate specialized agents
    - Manages execution order (dependencies, priority)
    - Aggregates results
    - Handles failures and retries
    - Provides real-time status tracking
    """
    
    def __init__(self):
        """Set up empty registries. Register agents before submitting work."""
        super().__init__(AgentType.COORDINATOR, "Task Coordinator")


        # Task management
        self.task_queue = PriorityQueue()  # (priority, task)
        self.task_registry: Dict[str, TaskMessage] = {}  # task_id -> TaskMessage
        self.task_status: Dict[str, TaskStatus] = {}  # task_id -> status
        self.task_results: Dict[str, TaskResult] = {}  # task_id -> result
        
        # Workflow tracking
        self.workflows: Dict[str, Dict[str, Any]] = {}  # workflow_id -> details
        self.task_to_workflow: Dict[str, str] = {}  # task_id -> workflow_id
        
        # Agent registry
        self.agents: Dict[AgentType, List[Agent]] = defaultdict(list)
        self.agent_status: Dict[str, str] = {}  # agent_id -> status
        
        # Retry logic
        self.max_retries = 3
        self.retry_count: Dict[str, int] = defaultdict(int)
        
        # Threading
        self.dispatch_thread = None
        self.is_running = False
        
    # =========================================================
    # AGENT MANAGEMENT
    # =========================================================
    
    def register_agent(self, agent: Agent) -> str:
        """
        Register a specialized agent with the coordinator.
        
        Returns:
            agent_id for tracking
        """
        agent_id = f"{agent.agent_type.value}_{len(self.agents[agent.agent_type])}"
        self.agents[agent.agent_type].append(agent)
        self.agent_status[agent_id] = "ready"
        print(f"✓ Agent registered: {agent_id}")
        return agent_id
    
    def get_available_agent(self, agent_type: AgentType) -> Optional[Agent]:
        """Get an available agent of given type"""
        agents = self.agents.get(agent_type, [])
        return agents[0] if agents else None
    
    # =========================================================
    # TASK SUBMISSION
    # =========================================================
    
    def submit_task(self, task: TaskMessage) -> str:
        """
        Submit a task to the coordinator.
        
        Returns:
            task_id for tracking
        """
        # Store task details
        self.task_registry[task.task_id] = task
        self.task_status[task.task_id] = TaskStatus.PENDING
        
        # Add to priority queue (negative priority for max-heap behavior)
        self.task_queue.put((-task.priority, task.task_id, task))
        
        print(f"📥 Task submitted: {task.task_id} | Action: {task.action} | Priority: {task.priority}")
        return task.task_id
    
    def submit_workflow(self, workflow_id: str, tasks: List[TaskMessage]) -> str:
        """
        Submit a multi-task workflow.
        
        Tasks are executed in order, respecting dependencies.
        Results are aggregated under workflow_id.
        
        Returns:
            workflow_id for tracking
        """
        self.workflows[workflow_id] = {
            "tasks": [t.task_id for t in tasks],
            "status": "in_progress",
            "created_at": datetime.now(),
            "results": {},
        }
        
        # Submit all tasks, building dependency chain
        for i, task in enumerate(tasks):
            if i > 0:
                # Each task depends on previous one
                task.dependencies.append(tasks[i-1].task_id)
            
            self.task_to_workflow[task.task_id] = workflow_id
            self.submit_task(task)
        
        print(f"📊 Workflow submitted: {workflow_id} with {len(tasks)} tasks")
        return workflow_id
    
    # =========================================================
    # TASK DISPATCHING & EXECUTION
    # =========================================================
    
    def start(self):
        """Start the coordinator dispatch loop"""
        if self.is_running:
            return
        
        self.is_running = True
        self.dispatch_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self.dispatch_thread.start()
        print("🚀 Coordinator started")
    
    def stop(self):
        """Stop the coordinator"""
        self.is_running = False
        if self.dispatch_thread:
            self.dispatch_thread.join(timeout=5)
        print("⏹️ Coordinator stopped")
    
    def _dispatch_loop(self):
        """Continuously pull tasks off the queue and dispatch them.

        Runs on a background thread until ``stop()`` is called.

        Blocks on the queue rather than polling it. The previous version spun
        on ``if self.task_queue.empty(): continue``, which pinned a CPU core
        at 100% for the entire life of the coordinator -- including while
        completely idle.
        """
        while self.is_running:
            try:
                # Blocks up to 1s, so an idle coordinator costs nothing and
                # stop() is still honoured within a second.
                try:
                    _, task_id, task = self.task_queue.get(timeout=1)
                except Empty:
                    continue

                # Not ready yet: put it back for a later pass. The short sleep
                # matters -- without it a task whose dependencies are still
                # running is popped and re-queued in a tight loop.
                if not self._check_dependencies(task):
                    self.task_queue.put((-task.priority, task_id, task))
                    time.sleep(0.05)
                    continue

                self._dispatch_task(task)

            except Exception as e:
                print(f"❌ Dispatch error: {e}")
                time.sleep(0.05)  # never spin on a repeating error
    
    def _check_dependencies(self, task: TaskMessage) -> bool:
        """Check if all task dependencies are completed"""
        for dep_id in task.dependencies:
            if dep_id not in self.task_results:
                return False
            if self.task_results[dep_id].status != TaskStatus.COMPLETED:
                return False
        return True
    
    def _dispatch_task(self, task: TaskMessage):
        """
        Find appropriate agent and execute task.
        """
        agent = self.get_available_agent(task.agent_type)
        
        if not agent:
            print(f"⚠️ No agent available for {task.agent_type.value}, retrying...")
            self.task_queue.put((-task.priority, task.task_id, task))
            return
        
        # Update status
        self.task_status[task.task_id] = TaskStatus.IN_PROGRESS
        
        # Execute (synchronous for now, can be async later)
        result = agent.handle_task(task)
        
        # Store result
        self.task_results[task.task_id] = result
        self.task_status[task.task_id] = result.status
        
        # Log to agent
        agent.log_result(result)
        
        # Handle workflow aggregation
        if task.task_id in self.task_to_workflow:
            workflow_id = self.task_to_workflow[task.task_id]
            self.workflows[workflow_id]["results"][task.task_id] = result
        
        print(f"✅ Task completed: {task.task_id} | Status: {result.status.value}")
        
        # Handle failures
        if result.status == TaskStatus.FAILED:
            self._handle_failure(task, result)
    
    def _handle_failure(self, task: TaskMessage, result: TaskResult):
        """
        Handle task failure with retry logic.
        """
        self.retry_count[task.task_id] += 1
        
        if self.retry_count[task.task_id] < self.max_retries:
            print(f"🔄 Retrying task {task.task_id} (attempt {self.retry_count[task.task_id] + 1})")
            self.task_status[task.task_id] = TaskStatus.PENDING
            # Re-submit to queue with same priority
            self.task_queue.put((-task.priority, task.task_id, task))
        else:
            print(f"❌ Task {task.task_id} failed permanently after {self.max_retries} retries")
    
    # =========================================================
    # ABSTRACT METHOD IMPLEMENTATION
    # =========================================================
    
    def execute(self, task: TaskMessage) -> TaskResult:
        """
        Coordinator doesn't execute tasks directly.
        This method shouldn't be called.
        """
        return TaskResult(
            task_id=task.task_id,
            agent_type=AgentType.COORDINATOR,
            status=TaskStatus.FAILED,
            error="Coordinator cannot execute tasks directly"
        )
    
    # =========================================================
    # STATUS & MONITORING
    # =========================================================
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        if task_id not in self.task_registry:
            return None
        
        task = self.task_registry[task_id]
        result = self.task_results.get(task_id)
        
        return {
            "task_id": task_id,
            "action": task.action,
            "agent_type": task.agent_type.value,
            "status": self.task_status[task_id].value,
            "result": result.to_dict() if result else None,
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of entire workflow"""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        task_results = [
            self.task_results[task_id].to_dict()
            for task_id in workflow["tasks"]
            if task_id in self.task_results
        ]
        
        return {
            "workflow_id": workflow_id,
            "status": workflow["status"],
            "total_tasks": len(workflow["tasks"]),
            "completed_tasks": len(task_results),
            "task_results": task_results,
            "created_at": workflow["created_at"].isoformat(),
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system health & metrics"""
        total_tasks = len(self.task_registry)
        completed = sum(1 for s in self.task_status.values() if s == TaskStatus.COMPLETED)
        failed = sum(1 for s in self.task_status.values() if s == TaskStatus.FAILED)
        
        return {
            "is_running": self.is_running,
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "pending_tasks": self.task_queue.qsize(),
            "workflows": len(self.workflows),
            "agents": {
                agent_type.value: len(agents)
                for agent_type, agents in self.agents.items()
                if agents
            },
            "timestamp": datetime.now().isoformat(),
        }
    
    def wait_for_workflow(self, workflow_id: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Block until workflow completes (useful for synchronous callers).
        
        Args:
            workflow_id: ID of workflow to wait for
            timeout: Max seconds to wait
            
        Returns:
            Workflow status dict
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            status = self.get_workflow_status(workflow_id)
            if status and status["completed_tasks"] == status["total_tasks"]:
                return status
            time.sleep(0.5)
        
        raise TimeoutError(f"Workflow {workflow_id} did not complete within {timeout}s")
