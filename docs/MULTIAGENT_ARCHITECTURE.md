# Multi-Agent Test Automation Framework - Implementation Guide

## 📋 Overview

This document describes the improved multi-agent architecture for the AI-Powered Test Automation framework. The system uses a **Coordinator-Worker pattern** where specialized agents work independently and report only to the central Coordinator.

---

## 🏗️ Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit UI / API Gateway                  │
│            (Task submission interface)                   │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ submit_task() / submit_workflow()
                   ▼
┌─────────────────────────────────────────────────────────┐
│         COORDINATOR AGENT (Manager)                      │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ • Task Router & Dispatcher                         │ │
│  │ • Priority Queue Manager                           │ │
│  │ • Dependency Resolver                              │ │
│  │ • Result Aggregator                                │ │
│  │ • Status Tracker                                   │ │
│  │ • Error Handler & Retry Logic                      │ │
│  └─────────────────────────────────────────────────────┘ │
└─┬──────────────────────────────────────────────────────┬─┘
  │                                                        │
  │ dispatch_task()                    poll_result()      │
  ▼                                                        ▼
[Test Executor]  [AI Generation]  [Report]  [Locator]  [Data]  [Performance]
   Agent            Agent          Agent    Repair      Validator  Analyzer
                                             Agent       Agent      Agent
```

### Communication Patterns

**Synchronous (Direct)**:
- UI → Coordinator: `submit_task()`, `get_task_status()`
- Coordinator → Worker Agent: `handle_task()`
- Worker Agent → Coordinator: Return `TaskResult`

**Data Flow**:
1. User submits task via UI
2. Coordinator adds to priority queue
3. Dispatch loop picks task
4. Routes to appropriate agent
5. Agent executes and returns result
6. Coordinator stores result
7. Result available for retrieval

---

## 🔧 Core Components

### 1. Agent Base Class (`agent_base.py`)

All agents inherit from `Agent` class.

**Key Methods**:
- `execute(task: TaskMessage) -> TaskResult`: Abstract - implement per agent
- `handle_task(task: TaskMessage) -> TaskResult`: Wrapper with error handling
- `log_result(result: TaskResult)`: Store result
- `get_result(task_id: str) -> TaskResult`: Retrieve stored result

**Example**:
```python
from framework.agent_base import Agent, AgentType, TaskMessage, TaskResult, TaskStatus

class MyCustomAgent(Agent):
    def __init__(self):
        super().__init__(AgentType.TEST_EXECUTOR, "My Agent")
    
    def execute(self, task: TaskMessage) -> TaskResult:
        # Implement custom logic here
        try:
            result = self._do_work(task.payload)
            return TaskResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                status=TaskStatus.COMPLETED,
                result=result,
            )
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                agent_type=self.agent_type,
                status=TaskStatus.FAILED,
                error=str(e),
            )
```

### 2. Coordinator Agent (`coordinator_agent.py`)

Central task dispatcher and result aggregator.

**Key Features**:
- **Priority Queue**: Tasks processed by priority + FIFO
- **Dependency Resolution**: Wait for upstream tasks to complete
- **Workflow Aggregation**: Multi-task workflows tracked together
- **Retry Logic**: Automatic retry on failure (configurable)
- **Status Tracking**: Real-time status for all tasks

**Key Methods**:
```python
# Submit single task
task_id = coordinator.submit_task(task)

# Submit multi-task workflow
workflow_id = coordinator.submit_workflow(workflow_id, [task1, task2, task3])

# Wait for completion (blocking)
status = coordinator.wait_for_workflow(workflow_id, timeout=300)

# Check status
task_status = coordinator.get_task_status(task_id)
workflow_status = coordinator.get_workflow_status(workflow_id)
system_status = coordinator.get_system_status()

# Agent management
coordinator.register_agent(agent)
coordinator.start()  # Start dispatch loop
coordinator.stop()   # Stop dispatch loop
```

### 3. Specialized Agents

#### TestExecutorAgent
**Purpose**: Execute test cases from Excel files

**Actions**:
- `run_test_cases`: Execute single test with optional data row
- `run_data_driven_test`: Execute test with multiple data sets

**Payload**:
```python
{
    "action": "run_test_cases",
    "payload": {
        "test_steps": [
            {"Description": "...", "XPath": "...", "Action": "...", "Data": "..."},
            ...
        ],
        "data_row": {"username": "test", "password": "pass"},
        "env": "DEV"
    }
}
```

**Result**:
```python
{
    "total_steps": 5,
    "passed_steps": 5,
    "failed_steps": 0,
    "success_rate": 100.0,
    "steps": [...],
    "environment": "DEV",
    "duration_sec": 12.5,
}
```

#### AIGenerationAgent
**Purpose**: Generate tests, data, and optimization suggestions via LLM

**Actions**:
- `generate_test_from_description`: NLP → Test steps
- `generate_test_data`: Create synthetic data based on schema
- `optimize_test_suite`: Suggest improvements
- `suggest_fix_for_failure`: AI-powered failure diagnosis

**Providers**: "stub" (mock), "openai", "claude", "local"

#### ReportAgent
**Purpose**: Generate reports in multiple formats

**Actions**:
- `generate_html_report`: Interactive HTML with metrics
- `generate_pdf_report`: PDF with charts
- `generate_summary`: Text summary

#### LocatorRepairAgent
**Purpose**: Self-healing for broken locators

**Actions**:
- `repair_xpath`: Suggest fixes for broken XPath
- `find_alternative_locator`: ML-based element discovery

#### DataValidatorAgent
**Purpose**: Test data quality validation

**Actions**:
- `validate_test_data`: Check format and values
- `detect_duplicates`: Find duplicate records
- `validate_schema`: Verify against expected schema

#### PerformanceAnalyzerAgent
**Purpose**: Performance metrics and bottleneck identification

**Actions**:
- `analyze_test_performance`: Extract metrics
- `identify_bottlenecks`: Find slow steps
- `generate_performance_report`: Comprehensive analysis

---

## 🚀 Usage Examples

### Example 1: Simple Test Execution

```python
from framework.coordinator_agent import CoordinatorAgent
from framework.test_executor_agent import TestExecutorAgent
from framework.agent_base import TaskMessage, AgentType

# Initialize
coordinator = CoordinatorAgent()
coordinator.register_agent(TestExecutorAgent())
coordinator.start()

# Create task
test_steps = [
    {"Description": "Open login", "XPath": "N/A", "Action": "launch_url", "Data": "https://example.com"},
    {"Description": "Enter user", "XPath": "//*[@id='user']", "Action": "enter_text", "Data": "testuser"},
]

task = TaskMessage(
    agent_type=AgentType.TEST_EXECUTOR,
    action="run_test_cases",
    payload={"test_steps": test_steps, "env": "DEV"}
)

# Submit and wait
task_id = coordinator.submit_task(task)
result = coordinator.task_results.get(task_id)  # Poll or wait

print(f"Status: {result.status}")
print(f"Passed: {result.result['passed_steps']}/{result.result['total_steps']}")
```

### Example 2: Multi-Task Workflow

```python
# Create 3 tasks that must run in sequence
tasks = [
    TaskMessage(agent_type=AgentType.AI_GENERATION, action="generate_test_from_description",
                payload={"description": "Login with valid credentials"}),
    TaskMessage(agent_type=AgentType.TEST_EXECUTOR, action="run_test_cases",
                payload={"test_steps": [...], "env": "TEST"}),
    TaskMessage(agent_type=AgentType.REPORT, action="generate_html_report",
                payload={"test_results": {...}, "filename": "test_report"}),
]

# Submit workflow
workflow_id = coordinator.submit_workflow("wf_001", tasks)

# Wait for completion
status = coordinator.wait_for_workflow(workflow_id, timeout=300)
print(f"Workflow result: {status}")
```

### Example 3: Parallel Task Execution

```python
# Submit multiple independent tasks (they run in parallel)
for i in range(5):
    task = TaskMessage(
        agent_type=AgentType.TEST_EXECUTOR,
        action="run_data_driven_test",
        payload={
            "test_steps": test_steps,
            "data_rows": data_sets[i],
            "env": "TEST"
        },
        priority=1 + (i % 3)  # Different priorities for staggered execution
    )
    coordinator.submit_task(task)

# Check system status
status = coordinator.get_system_status()
print(f"Pending: {status['pending_tasks']}, Completed: {status['completed_tasks']}")
```

### Example 4: Using Streamlit Integration

See `app_multiagent.py` for full Streamlit integration with:
- Real-time coordinator status dashboard
- Task submission forms
- Workflow result aggregation
- Multi-agent parallel execution monitoring

---

## 📊 Task Message Format

```python
TaskMessage(
    task_id="auto-generated-uuid",        # Optional, auto-generated
    agent_type=AgentType.TEST_EXECUTOR,   # Required: specifies which agent
    action="run_test_cases",              # Required: what to do
    payload={                             # Required: task-specific data
        "test_steps": [...],
        "data_row": {...},
        "env": "DEV"
    },
    priority=1,                           # Optional: default 0, higher = urgent
    dependencies=["task_id_1", "task_id_2"],  # Optional: must complete first
    created_at=datetime.now(),            # Auto-generated
    timeout=300                           # Seconds before timeout
)
```

---

## 🔄 Workflow Patterns

### Pattern 1: Sequential Dependency

```
Task 1: Generate test
   ↓ (waits for completion)
Task 2: Run test (uses generated test)
   ↓
Task 3: Generate report
```

```python
tasks = [task1, task2, task3]
coordinator.submit_workflow("seq_wf", tasks)
# Coordinator automatically sets dependencies: task2→task1, task3→task2
```

### Pattern 2: Fan-Out (Parallel)

```
Task 1: Run test with data set 1
Task 2: Run test with data set 2     (all run in parallel)
Task 3: Run test with data set 3
   ↓ (all complete)
Task 4: Aggregate results
```

```python
parallel_tasks = [task1, task2, task3]
for t in parallel_tasks:
    coordinator.submit_task(t)  # No dependencies = parallel execution

# After all complete, submit aggregation task
agg_task.dependencies = [task1.task_id, task2.task_id, task3.task_id]
coordinator.submit_task(agg_task)
```

### Pattern 3: Star Topology

```
       Task 1 (data prep)
          ↓
    ┌─────┼─────┐
    ↓     ↓     ↓
 Task 2  Task 3  Task 4 (all depend on Task 1)
    │     │      │
    └─────┼──────┘
        ↓
    Task 5 (aggregation)
```

---

## 🎯 Best Practices

### 1. Task Priority
```python
# Urgent tasks: priority 10
urgent_task.priority = 10

# Normal: priority 1 (default)
normal_task.priority = 1

# Background: priority -1
background_task.priority = -1

# Tasks processed by: priority DESC, then FIFO
```

### 2. Error Handling
```python
# Coordinator retries failed tasks (configurable max_retries)
coordinator.max_retries = 3

# Check for failures
result = coordinator.task_results[task_id]
if result.status == TaskStatus.FAILED:
    print(f"Error: {result.error}")
    print(f"Traceback: {result.metadata.get('traceback')}")
```

### 3. Monitoring
```python
# Real-time status
status = coordinator.get_system_status()
print(f"Active: {status['pending_tasks']}, Done: {status['completed_tasks']}")

# Per-task metrics
task_result = coordinator.get_task_status(task_id)
print(f"Duration: {task_result['result']['execution_time_ms']}ms")

# Workflow completion
try:
    wf_status = coordinator.wait_for_workflow(wf_id, timeout=300)
    print(f"Completed: {wf_status['completed_tasks']}/{wf_status['total_tasks']}")
except TimeoutError:
    print("Workflow still running")
```

### 4. Custom Agents
```python
from framework.agent_base import Agent, AgentType, TaskMessage, TaskResult, TaskStatus

class CustomAgent(Agent):
    def __init__(self):
        super().__init__(AgentType.TEST_EXECUTOR, "Custom")
    
    def execute(self, task: TaskMessage) -> TaskResult:
        # Your implementation
        pass

# Register and use
agent = CustomAgent()
coordinator.register_agent(agent)

task = TaskMessage(agent_type=AgentType.TEST_EXECUTOR, ...)
coordinator.submit_task(task)
```

---

## 📈 Performance Considerations

### Parallel Execution
- Independent tasks run in parallel via thread pool
- Max parallelism = number of agents registered per type
- Register multiple instances for higher throughput:
  ```python
  for i in range(5):
      coordinator.register_agent(TestExecutorAgent())  # 5 parallel executors
  ```

### Async Operations
- Coordinator dispatch loop runs in background thread
- Non-blocking for UI
- Results available via polling or `wait_for_workflow()`

### Scaling
- **In-Process**: Register multiple agent instances
- **Distributed (Future)**: Replace in-memory queue with Celery + RabbitMQ
- **Monitoring**: Extend Coordinator with metrics export (Prometheus)

---

## 🔌 Integration with Streamlit

The `app_multiagent.py` shows integration patterns:

```python
# Initialize once per session
@st.cache_resource
def initialize_system():
    coordinator = CoordinatorAgent()
    coordinator.register_agent(TestExecutorAgent())
    coordinator.register_agent(AIGenerationAgent())
    # ... more agents
    coordinator.start()
    return coordinator

coordinator = initialize_system()

# Submit task from UI
if st.button("Run Test"):
    task = TaskMessage(...)
    task_id = coordinator.submit_task(task)
    
    # Async wait in UI
    progress_bar = st.progress(0)
    while True:
        result = coordinator.task_results.get(task_id)
        if result:
            st.success(f"Complete: {result.status.value}")
            break
        progress_bar.progress(50)
        time.sleep(0.5)
```

---

## 📚 File Structure

```
src/ai_test_engine/
├── agent_base.py              # Base Agent class + enums
├── coordinator_agent.py        # Coordinator (Manager)
├── test_executor_agent.py      # Test execution
├── ai_generation_agent.py      # AI-powered generation
├── report_agent.py             # Report generation
├── specialized_agents.py       # Repair, Validation, Performance analysis
├── keyword_engine.py           # Existing keyword library
├── keyword_library.py          # Existing keywords
└── test_runner.py              # Legacy (can be deprecated)

app.py                          # Original Streamlit app
app_multiagent.py              # New multi-agent Streamlit app
```

---

## 🚦 Next Steps

### Phase 1 (Current)
- ✅ Coordinator Agent implementation
- ✅ Specialized agents (6 types)
- ✅ Streamlit integration
- ✅ Priority queue & dependency resolution
- ✅ Error handling & retry logic

### Phase 2 (Planned)
- [ ] Real LLM integration (OpenAI, Claude)
- [ ] Distributed queue (Celery + Redis)
- [ ] WebSocket real-time dashboard
- [ ] Metrics export (Prometheus)
- [ ] Test result caching
- [ ] Advanced retry strategies

### Phase 3 (Advanced)
- [ ] ML-based locator prediction
- [ ] Test flakiness detection
- [ ] Cross-environment orchestration
- [ ] Visual regression testing
- [ ] CI/CD pipeline integration

---

## 📞 Support & Debugging

### Enable Debug Logging
```python
coordinator.is_running = True
# Print statements show task flow
# Reports are written to outputs/reports/
```

### Inspect Agent Status
```python
status = coordinator.get_system_status()
print(json.dumps(status, indent=2))
```

### Check Task Result Details
```python
result = coordinator.task_results[task_id]
print(f"Status: {result.status}")
print(f"Error: {result.error}")
print(f"Traceback: {result.metadata.get('traceback')}")
```

---

**Version**: 1.0  
**Last Updated**: 2024  
**Author**: AI Engineering Team
