# Quick Start Guide - Multi-Agent Test Automation

## 🎯 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install streamlit pandas selenium webdriver-manager requests fpdf matplotlib
# For LLM integration (optional):
# pip install openai anthropic
```

### Step 2: Run Streamlit App
```bash
streamlit run app_multiagent.py
```

Then navigate to:
- **Dashboard**: System Status & Task Monitoring
- **Run Tests**: Upload Excel files and execute
- **AI Features**: Generate tests, data, optimizations
- **Self-Healing**: Repair broken locators
- **Validation**: Check test data quality
- **Performance**: Analyze test execution metrics

---

## 💡 Common Usage Patterns

### Use Case 1: Single Test Execution

```python
from framework.coordinator_agent import CoordinatorAgent
from framework.test_executor_agent import TestExecutorAgent
from framework.agent_base import TaskMessage, AgentType

# Setup
coordinator = CoordinatorAgent()
coordinator.register_agent(TestExecutorAgent())
coordinator.start()

# Create test
test_steps = [
    {"Description": "Go to login", "XPath": "N/A", "Action": "launch_url", "Data": "https://example.com/login"},
    {"Description": "Enter username", "XPath": "//*[@id='username']", "Action": "enter_text", "Data": "admin"},
    {"Description": "Enter password", "XPath": "//*[@id='password']", "Action": "enter_text", "Data": "pass123"},
    {"Description": "Click login", "XPath": "//*[@id='submit']", "Action": "click", "Data": ""},
]

# Execute
task = TaskMessage(
    agent_type=AgentType.TEST_EXECUTOR,
    action="run_test_cases",
    payload={"test_steps": test_steps, "env": "DEV"},
    priority=1
)

task_id = coordinator.submit_task(task)

# Wait for result
while True:
    result = coordinator.task_results.get(task_id)
    if result:
        print(f"✅ Test completed: {result.result['passed_steps']}/{result.result['total_steps']} passed")
        break
    time.sleep(0.5)

coordinator.stop()
```

---

### Use Case 2: Data-Driven Testing (Multiple Data Sets)

```python
# Multiple iterations with different data
data_rows = [
    {"username": "user1", "password": "pass1"},
    {"username": "user2", "password": "pass2"},
    {"username": "user3", "password": "pass3"},
]

test_steps = [
    {"Description": "Open login", "XPath": "N/A", "Action": "launch_url", "Data": "https://example.com"},
    {"Description": "Enter {{username}}", "XPath": "//*[@id='user']", "Action": "enter_text", "Data": "{{username}}"},
    {"Description": "Enter {{password}}", "XPath": "//*[@id='pass']", "Action": "enter_text", "Data": "{{password}}"},
]

task = TaskMessage(
    agent_type=AgentType.TEST_EXECUTOR,
    action="run_data_driven_test",
    payload={
        "test_steps": test_steps,
        "data_rows": data_rows,
        "env": "TEST"
    }
)

task_id = coordinator.submit_task(task)
result = coordinator.task_results.get(task_id)
print(f"Total: {result.result['total_steps_executed']} steps")
print(f"Passed: {result.result['total_passed']}")
```

---

### Use Case 3: AI Test Generation

```python
# Describe what you want to test
description = "Login with valid credentials and verify dashboard displays"

task = TaskMessage(
    agent_type=AgentType.AI_GENERATION,
    action="generate_test_from_description",
    payload={"description": description}
)

task_id = coordinator.submit_task(task)

result = coordinator.task_results.get(task_id)
generated_steps = result.result

# Now use generated steps to run test
exec_task = TaskMessage(
    agent_type=AgentType.TEST_EXECUTOR,
    action="run_test_cases",
    payload={"test_steps": generated_steps}
)

coordinator.submit_task(exec_task)
```

---

### Use Case 4: Multi-Step Workflow

```python
# 1. Generate test from description
task1 = TaskMessage(
    agent_type=AgentType.AI_GENERATION,
    action="generate_test_from_description",
    payload={"description": "Login test"}
)

# 2. Run the generated test (depends on task 1)
task2 = TaskMessage(
    agent_type=AgentType.TEST_EXECUTOR,
    action="run_test_cases",
    payload={"test_steps": []}  # Will use result from task1
)

# 3. Generate report (depends on task 2)
task3 = TaskMessage(
    agent_type=AgentType.REPORT,
    action="generate_html_report",
    payload={"test_results": {}}  # Will use result from task2
)

# Submit as workflow
workflow_id = coordinator.submit_workflow("login_workflow", [task1, task2, task3])

# Wait for all to complete
status = coordinator.wait_for_workflow(workflow_id, timeout=120)
print(f"Workflow complete: {status['completed_tasks']}/{status['total_tasks']} tasks")
```

---

### Use Case 5: Validate Test Data

```python
# Load test data
import pandas as pd
df = pd.read_excel("test_data.xlsx")
data = df.to_dict(orient="records")

# Check for duplicates
task1 = TaskMessage(
    agent_type=AgentType.DATA_VALIDATOR,
    action="detect_duplicates",
    payload={"data": data}
)

# Validate quality
task2 = TaskMessage(
    agent_type=AgentType.DATA_VALIDATOR,
    action="validate_test_data",
    payload={"data": data}
)

t1_id = coordinator.submit_task(task1)
t2_id = coordinator.submit_task(task2)

# Check results
dup_result = coordinator.task_results[t1_id]
print(f"Duplicates found: {dup_result.result['duplicate_count']}")

val_result = coordinator.task_results[t2_id]
print(f"Quality score: {val_result.result['quality_score']:.0%}")
```

---

### Use Case 6: Self-Healing Locators

```python
# Locator failed during execution
broken_xpath = "//*[@id='submit-btn']"
error = "Element not found"

task = TaskMessage(
    agent_type=AgentType.LOCATOR_REPAIR,
    action="repair_xpath",
    payload={
        "original_xpath": broken_xpath,
        "error": error,
        "dom_snapshot": ""  # Optional: pass HTML snapshot for analysis
    }
)

task_id = coordinator.submit_task(task)

result = coordinator.task_results[task_id]
suggestions = result.result['suggestions']

for sugg in suggestions:
    print(f"Try: {sugg['xpath']} (Strategy: {sugg['strategy']}, Confidence: {sugg['confidence']})")
```

---

### Use Case 7: Performance Analysis

```python
# Run a test first
test_result = {...}  # From previous execution

# Analyze performance
task = TaskMessage(
    agent_type=AgentType.PERFORMANCE_ANALYZER,
    action="analyze_test_performance",
    payload={"test_results": test_result}
)

task_id = coordinator.submit_task(task)

perf_result = coordinator.task_results[task_id]
print(f"Total duration: {perf_result.result['total_duration_sec']:.2f}s")
print(f"Average step: {perf_result.result['avg_step_duration_ms']:.0f}ms")

# Find slow steps
bottleneck_task = TaskMessage(
    agent_type=AgentType.PERFORMANCE_ANALYZER,
    action="identify_bottlenecks",
    payload={"test_results": test_result, "threshold_ms": 500}
)

coordinator.submit_task(bottleneck_task)
```

---

## 🔄 Running Tests from Command Line

### Example Script: `run_tests.py`

```python
#!/usr/bin/env python3
"""Command-line test runner using multi-agent coordinator"""

import sys
import json
import pandas as pd
from framework.coordinator_agent import CoordinatorAgent
from framework.test_executor_agent import TestExecutorAgent
from framework.report_agent import ReportAgent
from framework.agent_base import TaskMessage, AgentType

def main():
    # Read test file from command line
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py <excel_file>")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    env = sys.argv[2] if len(sys.argv) > 2 else "DEV"
    
    print(f"📊 Reading test file: {excel_file}")
    
    # Initialize coordinator
    coordinator = CoordinatorAgent()
    coordinator.register_agent(TestExecutorAgent())
    coordinator.register_agent(ReportAgent())
    coordinator.start()
    
    # Read Excel
    df = pd.read_excel(excel_file)
    test_steps = df.to_dict(orient="records")
    
    # Run test
    task = TaskMessage(
        agent_type=AgentType.TEST_EXECUTOR,
        action="run_test_cases",
        payload={"test_steps": test_steps, "env": env},
        priority=1
    )
    
    task_id = coordinator.submit_task(task)
    print(f"🚀 Task submitted: {task_id}")
    
    # Generate report
    report_task = TaskMessage(
        agent_type=AgentType.REPORT,
        action="generate_html_report",
        payload={
            "test_results": {},  # Will be filled from test task
            "filename": f"{excel_file}_report",
            "title": f"Test Report - {env}"
        },
        dependencies=[task_id],  # Depends on test completion
        priority=2
    )
    
    report_task_id = coordinator.submit_task(report_task)
    
    # Wait for completion
    try:
        # Wait for test
        while True:
            result = coordinator.task_results.get(task_id)
            if result:
                print(f"✅ Test: {result.result['passed_steps']}/{result.result['total_steps']} passed")
                break
            import time; time.sleep(0.5)
        
        # Wait for report
        while True:
            result = coordinator.task_results.get(report_task_id)
            if result:
                print(f"📄 Report: {result.result['filepath']}")
                break
            import time; time.sleep(0.5)
    
    finally:
        coordinator.stop()

if __name__ == "__main__":
    main()
```

Run it:
```bash
python run_tests.py tests/login_test.xlsx DEV
python run_tests.py tests/checkout_test.xlsx PROD
```

---

## 📊 Monitoring & Debugging

### Check System Status
```python
status = coordinator.get_system_status()
print(json.dumps(status, indent=2))

# Output:
# {
#   "is_running": true,
#   "total_tasks": 5,
#   "completed_tasks": 2,
#   "failed_tasks": 0,
#   "pending_tasks": 3,
#   "workflows": 1,
#   "agents": {
#     "test_executor": 1,
#     "ai_generation": 1,
#     "report": 1,
#     ...
#   }
# }
```

### Check Task Status
```python
task_status = coordinator.get_task_status(task_id)
print(json.dumps(task_status, indent=2))
```

### Check Workflow Status
```python
workflow_status = coordinator.get_workflow_status(workflow_id)
print(f"Completed: {workflow_status['completed_tasks']}/{workflow_status['total_tasks']}")
```

---

## 🐛 Troubleshooting

### Task Not Progressing
```python
# Check if coordinator is running
print(coordinator.is_running)

# Check queue size
print(coordinator.task_queue.qsize())

# Check if agents are registered
print(coordinator.get_system_status()['agents'])
```

### Task Failed
```python
result = coordinator.task_results[task_id]
if result.status == TaskStatus.FAILED:
    print(f"Error: {result.error}")
    print(f"Details: {result.metadata}")
```

### Retry Logic
```python
# Configure max retries
coordinator.max_retries = 5  # Default is 3
```

---

## 📚 More Examples

For more examples, see:
- `app_multiagent.py` - Streamlit UI examples
- `MULTIAGENT_ARCHITECTURE.md` - Detailed documentation
- `framework/` - Agent implementations

---

## 🚀 Next Steps

1. ✅ Basic test execution
2. → Integrate real LLM for AI features
3. → Add distributed queue for scaling
4. → Build monitoring dashboard
5. → Deploy to production

---

**Happy Testing! 🎉**
