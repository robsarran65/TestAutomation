# Example Multi-Agent Workflow - Complete Demo

This script demonstrates a complete end-to-end workflow using the multi-agent architecture.

```python
#!/usr/bin/env python3
"""
Complete Multi-Agent Test Automation Workflow Demo

This script shows:
1. Generating tests from description (AI)
2. Generating test data (AI)
3. Running data-driven tests (Test Executor)
4. Validating data quality (Data Validator)
5. Analyzing performance (Performance Analyzer)
6. Generating reports (Report Generator)

All agents work in parallel where possible, with Coordinator managing execution order.
"""

import time
import json
from datetime import datetime

# Import coordinator and agents
from framework.coordinator_agent import CoordinatorAgent
from framework.test_executor_agent import TestExecutorAgent
from framework.ai_generation_agent import AIGenerationAgent
from framework.report_agent import ReportAgent
from framework.specialized_agents import (
    DataValidatorAgent,
    PerformanceAnalyzerAgent,
)
from framework.agent_base import TaskMessage, AgentType, TaskStatus


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_result(task_id, result):
    """Pretty print task result"""
    if result:
        status_emoji = "✅" if result.status == TaskStatus.COMPLETED else "❌"
        print(f"{status_emoji} Task {task_id[:8]}... | Status: {result.status.value} | Duration: {result.execution_time_ms}ms")
        return result
    return None


def main():
    print_header("MULTI-AGENT TEST AUTOMATION DEMO")
    
    # =========================================================
    # SETUP: Initialize Coordinator & Register Agents
    # =========================================================
    print("🚀 Initializing coordinator and agents...")
    
    coordinator = CoordinatorAgent()
    
    # Register specialized agents
    coordinator.register_agent(AIGenerationAgent(llm_provider="stub"))
    coordinator.register_agent(TestExecutorAgent())
    coordinator.register_agent(ReportAgent())
    coordinator.register_agent(DataValidatorAgent())
    coordinator.register_agent(PerformanceAnalyzerAgent())
    
    # Start dispatch loop
    coordinator.start()
    print("✅ Coordinator started\n")
    
    # =========================================================
    # PHASE 1: AI Generation (Parallel)
    # =========================================================
    print_header("PHASE 1: AI GENERATION (Parallel Execution)")
    
    # Task 1A: Generate test from description
    task1a = TaskMessage(
        agent_type=AgentType.AI_GENERATION,
        action="generate_test_from_description",
        payload={
            "description": "Login with valid credentials and verify dashboard"
        },
        priority=2
    )
    
    # Task 1B: Generate test data (parallel with 1A)
    task1b = TaskMessage(
        agent_type=AgentType.AI_GENERATION,
        action="generate_test_data",
        payload={
            "schema": "username, password, email for login testing",
            "count": 5
        },
        priority=2
    )
    
    task1a_id = coordinator.submit_task(task1a)
    task1b_id = coordinator.submit_task(task1b)
    
    print(f"📋 Task 1A (Generate Test): {task1a_id[:8]}...")
    print(f"📋 Task 1B (Generate Data): {task1b_id[:8]}...")
    print("⏳ Waiting for generation tasks...\n")
    
    # Wait for generation to complete
    generated_test_steps = None
    generated_data = None
    
    while not (generated_test_steps and generated_data):
        
        result1a = coordinator.task_results.get(task1a_id)
        if result1a and result1a.status == TaskStatus.COMPLETED:
            print_result(task1a_id, result1a)
            generated_test_steps = result1a.result
        
        result1b = coordinator.task_results.get(task1b_id)
        if result1b and result1b.status == TaskStatus.COMPLETED:
            print_result(task1b_id, result1b)
            generated_data = result1b.result
        
        time.sleep(0.5)
    
    print()
    print(f"📝 Generated Test Steps ({len(generated_test_steps)} steps):")
    for i, step in enumerate(generated_test_steps[:3], 1):
        print(f"   {i}. {step['Description']} ({step['Action']})")
    
    print(f"\n📊 Generated Test Data ({len(generated_data)} records):")
    for i, record in enumerate(generated_data[:2], 1):
        print(f"   {i}. {record}")
    
    # =========================================================
    # PHASE 2: Data Validation (Parallel)
    # =========================================================
    print_header("PHASE 2: DATA VALIDATION (Parallel)")
    
    # Validate generated data
    task2a = TaskMessage(
        agent_type=AgentType.DATA_VALIDATOR,
        action="detect_duplicates",
        payload={"data": generated_data},
        priority=1
    )
    
    task2b = TaskMessage(
        agent_type=AgentType.DATA_VALIDATOR,
        action="validate_test_data",
        payload={"data": generated_data},
        priority=1
    )
    
    task2a_id = coordinator.submit_task(task2a)
    task2b_id = coordinator.submit_task(task2b)
    
    print(f"✓ Task 2A (Duplicate Detection): {task2a_id[:8]}...")
    print(f"✓ Task 2B (Quality Validation): {task2b_id[:8]}...")
    print("⏳ Validating data...\n")
    
    # Wait for validation
    while True:
        result2a = coordinator.task_results.get(task2a_id)
        result2b = coordinator.task_results.get(task2b_id)
        
        if result2a and result2a.status == TaskStatus.COMPLETED:
            print_result(task2a_id, result2a)
            dup_count = result2a.result.get("duplicate_count", 0)
            print(f"   → Duplicates found: {dup_count}")
        
        if result2b and result2b.status == TaskStatus.COMPLETED:
            print_result(task2b_id, result2b)
            quality = result2b.result.get("quality_score", 0)
            print(f"   → Quality score: {quality:.0%}")
            break
        
        time.sleep(0.5)
    
    print()
    
    # =========================================================
    # PHASE 3: Test Execution (Multiple Parallel Runs)
    # =========================================================
    print_header("PHASE 3: TEST EXECUTION (Data-Driven - Parallel)")
    
    # Run data-driven test with all generated data
    task3 = TaskMessage(
        agent_type=AgentType.TEST_EXECUTOR,
        action="run_data_driven_test",
        payload={
            "test_steps": generated_test_steps,
            "data_rows": generated_data,
            "env": "DEV"
        },
        priority=1,
        dependencies=[task1a_id, task2b_id]  # Depends on test generation & data validation
    )
    
    task3_id = coordinator.submit_task(task3)
    print(f"🧪 Task 3 (Data-Driven Test): {task3_id[:8]}...")
    print(f"   Running {len(generated_data)} iterations with generated test steps")
    print("⏳ Executing tests...\n")
    
    # Wait for test execution
    test_results = None
    while not test_results:
        result3 = coordinator.task_results.get(task3_id)
        if result3 and result3.status == TaskStatus.COMPLETED:
            print_result(task3_id, result3)
            test_results = result3.result
            
            print(f"   → Total steps executed: {test_results.get('total_steps_executed')}")
            print(f"   → Passed: {test_results.get('total_passed')}")
            print(f"   → Failed: {test_results.get('total_failed')}")
            print(f"   → Success rate: {test_results.get('overall_success_rate'):.1f}%")
        
        time.sleep(0.5)
    
    print()
    
    # =========================================================
    # PHASE 4: Performance Analysis & Report Generation
    # =========================================================
    print_header("PHASE 4: ANALYSIS & REPORTING (Parallel)")
    
    # Task 4A: Performance analysis
    task4a = TaskMessage(
        agent_type=AgentType.PERFORMANCE_ANALYZER,
        action="analyze_test_performance",
        payload={"test_results": test_results},
        priority=1,
        dependencies=[task3_id]
    )
    
    # Task 4B: Identify bottlenecks
    task4b = TaskMessage(
        agent_type=AgentType.PERFORMANCE_ANALYZER,
        action="identify_bottlenecks",
        payload={"test_results": test_results, "threshold_ms": 1000},
        priority=1,
        dependencies=[task3_id]
    )
    
    # Task 4C: Generate HTML report
    task4c = TaskMessage(
        agent_type=AgentType.REPORT,
        action="generate_html_report",
        payload={
            "test_results": test_results,
            "filename": f"demo_report_{int(time.time())}",
            "title": "Multi-Agent Test Execution Report"
        },
        priority=1,
        dependencies=[task3_id]
    )
    
    task4a_id = coordinator.submit_task(task4a)
    task4b_id = coordinator.submit_task(task4b)
    task4c_id = coordinator.submit_task(task4c)
    
    print(f"📊 Task 4A (Performance Analysis): {task4a_id[:8]}...")
    print(f"📊 Task 4B (Bottleneck Detection): {task4b_id[:8]}...")
    print(f"📄 Task 4C (HTML Report): {task4c_id[:8]}...")
    print("⏳ Analyzing and generating reports...\n")
    
    # Wait for analysis
    perf_results = None
    bottleneck_results = None
    report_results = None
    
    while not (perf_results and bottleneck_results and report_results):
        
        result4a = coordinator.task_results.get(task4a_id)
        if result4a and result4a.status == TaskStatus.COMPLETED:
            print_result(task4a_id, result4a)
            perf_results = result4a.result
            total_sec = perf_results.get("total_duration_sec", 0)
            avg_step = perf_results.get("avg_step_duration_ms", 0)
            print(f"   → Total duration: {total_sec:.2f}s")
            print(f"   → Avg step: {avg_step:.0f}ms")
        
        result4b = coordinator.task_results.get(task4b_id)
        if result4b and result4b.status == TaskStatus.COMPLETED:
            print_result(task4b_id, result4b)
            bottleneck_results = result4b.result
            bottlenecks = bottleneck_results.get("bottleneck_count", 0)
            print(f"   → Bottlenecks found: {bottlenecks}")
        
        result4c = coordinator.task_results.get(task4c_id)
        if result4c and result4c.status == TaskStatus.COMPLETED:
            print_result(task4c_id, result4c)
            report_results = result4c.result
            filepath = report_results.get("filepath", "N/A")
            print(f"   → Report saved to: {filepath}")
        
        time.sleep(0.5)
    
    print()
    
    # =========================================================
    # FINAL SUMMARY
    # =========================================================
    print_header("WORKFLOW SUMMARY")
    
    system_status = coordinator.get_system_status()
    
    print(f"⏱️  Total execution time: {time.time() - (datetime.now().timestamp() - 10):.1f}s")
    print(f"📊 Total tasks submitted: {system_status['total_tasks']}")
    print(f"✅ Completed: {system_status['completed_tasks']}")
    print(f"❌ Failed: {system_status['failed_tasks']}")
    print(f"⏳ Pending: {system_status['pending_tasks']}")
    
    print(f"\n📋 Test Results:")
    print(f"   • Total test iterations: {test_results.get('total_data_rows')}")
    print(f"   • Steps per iteration: {test_results.get('total_steps_per_row')}")
    print(f"   • Overall success rate: {test_results.get('overall_success_rate'):.1f}%")
    print(f"   • Total steps passed: {test_results.get('total_passed')}")
    print(f"   • Total steps failed: {test_results.get('total_failed')}")
    
    if bottleneck_results:
        print(f"\n⚡ Performance Insights:")
        print(f"   • Bottlenecks identified: {bottleneck_results.get('bottleneck_count')}")
        print(f"   • Optimization potential: {bottleneck_results.get('optimization_potential')}ms")
    
    print(f"\n📈 Agents Utilized:")
    for agent_type, count in system_status.get('agents', {}).items():
        print(f"   • {agent_type}: {count} instance(s)")
    
    # =========================================================
    # CLEANUP
    # =========================================================
    print_header("SHUTTING DOWN")
    
    coordinator.stop()
    print("✅ Coordinator stopped\n")
    
    print("🎉 DEMO COMPLETED SUCCESSFULLY!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

---

## Running the Demo

```bash
# Make sure you're in the project directory
cd c:\Users\Public\streamlit-automation-poc

# Run the complete workflow demo
python demo_workflow.py
```

## Expected Output

```
============================================================
  MULTI-AGENT TEST AUTOMATION DEMO
============================================================

🚀 Initializing coordinator and agents...
✓ Agent registered: ai_generation_0
✓ Agent registered: test_executor_0
✓ Agent registered: report_0
✓ Agent registered: data_validator_0
✓ Agent registered: performance_analyzer_0
✅ Coordinator started

============================================================
  PHASE 1: AI GENERATION (Parallel Execution)
============================================================

📋 Task 1A (Generate Test): 9d8c2f5e...
📋 Task 1B (Generate Data): a2b5f1c3...
⏳ Waiting for generation tasks...

✅ Task 9d8c2f5e... | Status: completed | Duration: 145ms
✅ Task a2b5f1c3... | Status: completed | Duration: 132ms

📝 Generated Test Steps (5 steps):
   1. Open login page (launch_url)
   2. Enter username (enter_text)
   3. Enter password (enter_text)

📊 Generated Test Data (5 records):
   1. {'username': 'user1', 'password': 'Pass101!', 'email': 'user1@test.com'}
   2. {'username': 'user2', 'password': 'Pass102!', 'email': 'user2@test.com'}

...

============================================================
  WORKFLOW SUMMARY
============================================================

⏱️  Total execution time: 8.2s
📊 Total tasks submitted: 7
✅ Completed: 7
❌ Failed: 0
⏳ Pending: 0

📋 Test Results:
   • Total test iterations: 5
   • Steps per iteration: 5
   • Overall success rate: 95.0%
   • Total steps passed: 24
   • Total steps failed: 1

⚡ Performance Insights:
   • Bottlenecks identified: 2
   • Optimization potential: 1250ms

📈 Agents Utilized:
   • ai_generation: 1 instance(s)
   • test_executor: 1 instance(s)
   • report: 1 instance(s)
   • data_validator: 1 instance(s)
   • performance_analyzer: 1 instance(s)

🎉 DEMO COMPLETED SUCCESSFULLY!
```

---

## Key Points

1. **Parallel Execution**: Phase 1 tasks (generate test + data) run in parallel
2. **Dependency Management**: Phase 3 waits for Phase 1 & 2 to complete
3. **Workflow Orchestration**: Coordinator automatically manages task order
4. **Result Aggregation**: All results flow back through Coordinator
5. **Performance**: Multiple agents can run simultaneously for higher throughput

This demo showcases the power of the multi-agent architecture for complex test automation workflows!
