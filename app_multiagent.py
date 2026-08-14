# =========================================================
# UPDATED STREAMLIT APP - Multi-Agent Architecture
# =========================================================

import streamlit as st
import pandas as pd
from io import BytesIO
import time
import json

# Import coordinator and agents
from framework.coordinator_agent import CoordinatorAgent
from framework.agent_base import TaskMessage, AgentType, TaskStatus
from framework.test_executor_agent import TestExecutorAgent
from framework.ai_generation_agent import AIGenerationAgent
from framework.report_agent import ReportAgent
from framework.specialized_agents import (
    LocatorRepairAgent,
    DataValidatorAgent,
    PerformanceAnalyzerAgent
)

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="AI‑Powered Test Automation - Multi-Agent",
    layout="wide"
)

st.title("🤖 AI‑Powered Test Automation (Multi-Agent Architecture)")

# =========================================================
# INITIALIZE COORDINATOR & AGENTS (Session State)
# =========================================================
@st.cache_resource
def initialize_system():
    """Initialize coordinator and agent pool - runs once per session"""
    
    print("=" * 60)
    print("Initializing Multi-Agent System")
    print("=" * 60)
    
    coordinator = CoordinatorAgent()
    
    # Register agents (can instantiate multiple of same type for parallel processing)
    coordinator.register_agent(TestExecutorAgent())
    coordinator.register_agent(AIGenerationAgent(llm_provider="stub"))
    coordinator.register_agent(ReportAgent())
    coordinator.register_agent(LocatorRepairAgent())
    coordinator.register_agent(DataValidatorAgent())
    coordinator.register_agent(PerformanceAnalyzerAgent())
    
    # Start dispatch loop
    coordinator.start()
    
    return coordinator

coordinator = initialize_system()

# =========================================================
# SIDEBAR NAVIGATION
# =========================================================
st.sidebar.header("🎯 Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "📊 System Dashboard",
        "🧪 Run Test Cases",
        "🧠 AI: Generate Test",
        "📈 AI: Generate Data",
        "🔧 Locator Repair",
        "✓ Data Validation",
        "⏱️ Performance Analysis",
    ]
)

# =========================================================
# SIDEBAR ENVIRONMENT & COORDINATOR STATUS
# =========================================================
st.sidebar.header("⚙️ Configuration")
env = st.sidebar.selectbox("Select environment", ["DEV", "TEST", "PROD"])
st.sidebar.write(f"Environment: **{env}**")

st.sidebar.divider()

st.sidebar.header("📡 Coordinator Status")
system_status = coordinator.get_system_status()

col1, col2 = st.sidebar.columns(2)
col1.metric("Active Tasks", system_status["pending_tasks"])
col2.metric("Completed", system_status["completed_tasks"])

col1, col2 = st.sidebar.columns(2)
col1.metric("Failed", system_status["failed_tasks"])
col2.metric("Workflows", system_status["workflows"])

# =========================================================
# PAGE 1 — SYSTEM DASHBOARD
# =========================================================
if page == "📊 System Dashboard":
    st.header("System Status & Monitoring")
    
    status = coordinator.get_system_status()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tasks", status["total_tasks"])
    col2.metric("Completed", status["completed_tasks"], delta=None)
    col3.metric("Failed", status["failed_tasks"], delta=None)
    col4.metric("Pending", status["pending_tasks"])
    
    st.divider()
    
    st.subheader("Registered Agents")
    agents_info = status.get("agents", {})
    
    agent_data = []
    for agent_type, count in agents_info.items():
        agent_data.append({"Agent Type": agent_type.replace("_", " ").title(), "Instances": count})
    
    if agent_data:
        st.dataframe(pd.DataFrame(agent_data), use_container_width=True)
    
    st.divider()
    
    st.subheader("Task Tracking")
    
    task_id_input = st.text_input("Enter Task ID to check status", "")
    if task_id_input:
        task_status = coordinator.get_task_status(task_id_input)
        if task_status:
            st.json(task_status)
        else:
            st.warning(f"Task {task_id_input} not found")
    
    workflow_id_input = st.text_input("Enter Workflow ID to check status", "")
    if workflow_id_input:
        workflow_status = coordinator.get_workflow_status(workflow_id_input)
        if workflow_status:
            st.json(workflow_status)
        else:
            st.warning(f"Workflow {workflow_id_input} not found")


# =========================================================
# PAGE 2 — RUN TEST CASES
# =========================================================
elif page == "🧪 Run Test Cases":
    st.header("📄 Upload & Run Test Cases")
    
    uploaded_files = st.file_uploader(
        "Upload one or more Excel test files",
        type=["xlsx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        if st.button("🚀 Run All Tests (via Coordinator)"):
            with st.spinner("Running tests through Multi-Agent system..."):
                
                # Create workflow with multiple tasks
                workflow_id = f"workflow_{int(time.time() * 1000)}"
                workflow_tasks = []
                
                for file in uploaded_files:
                    # Read Excel file
                    df = pd.read_excel(file)
                    test_steps = df.to_dict(orient="records")
                    
                    # Create task for each file
                    task = TaskMessage(
                        agent_type=AgentType.TEST_EXECUTOR,
                        action="run_test_cases",
                        payload={
                            "test_steps": test_steps,
                            "data_row": {},
                            "env": env,
                        },
                        priority=1,
                    )
                    workflow_tasks.append(task)
                
                # Submit workflow to coordinator
                coordinator.submit_workflow(workflow_id, workflow_tasks)
                
                st.success(f"✅ Workflow submitted: {workflow_id}")
                st.info(f"📊 {len(workflow_tasks)} test execution tasks queued")
                
                # Wait for workflow completion (with timeout)
                try:
                    workflow_status = coordinator.wait_for_workflow(workflow_id, timeout=120)
                    
                    # Display results
                    st.success("✅ Workflow completed!")
                    
                    st.json(workflow_status)
                    
                except TimeoutError:
                    st.warning("⏱️ Workflow is still running. Check dashboard for updates.")
                    st.write(f"Workflow ID: `{workflow_id}`")


# =========================================================
# PAGE 3 — AI: GENERATE TEST
# =========================================================
elif page == "🧠 AI: Generate Test":
    st.header("🧠 AI: Generate Test From Description")
    
    description = st.text_area(
        "Describe the test you want (e.g., 'Login with valid credentials')"
    )
    
    if st.button("Generate Test Steps"):
        if description.strip():
            with st.spinner("Generating test steps via AI Agent..."):
                
                task = TaskMessage(
                    agent_type=AgentType.AI_GENERATION,
                    action="generate_test_from_description",
                    payload={"description": description},
                    priority=2,
                )
                
                task_id = coordinator.submit_task(task)
                st.info(f"📋 Task submitted: {task_id}")
                
                # Wait for result
                start_time = time.time()
                while time.time() - start_time < 30:
                    result = coordinator.task_results.get(task_id)
                    if result:
                        if result.status == TaskStatus.COMPLETED:
                            df = pd.DataFrame(result.result)
                            st.subheader("Generated Test Steps")
                            st.dataframe(df, use_container_width=True)
                            
                            # Download as Excel
                            buffer = BytesIO()
                            df.to_excel(buffer, index=False, engine="openpyxl")
                            buffer.seek(0)
                            
                            st.download_button(
                                "📥 Download as Excel",
                                data=buffer,
                                file_name="generated_test.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            break
                        elif result.status == TaskStatus.FAILED:
                            st.error(f"Task failed: {result.error}")
                            break
                    
                    time.sleep(0.5)
                else:
                    st.warning("Task still processing, check dashboard")
        
        else:
            st.warning("Please enter a description.")


# =========================================================
# PAGE 4 — AI: GENERATE DATA
# =========================================================
elif page == "📈 AI: Generate Data":
    st.header("🧠 AI: Generate Test Data")
    
    col1, col2 = st.columns(2)
    with col1:
        schema = st.text_input(
            "Describe the data you need (e.g., 'usernames and passwords')"
        )
    with col2:
        count = st.number_input("How many records?", min_value=1, max_value=100, value=5)
    
    if st.button("Generate Data"):
        if schema.strip():
            with st.spinner("Generating test data via AI Agent..."):
                
                task = TaskMessage(
                    agent_type=AgentType.AI_GENERATION,
                    action="generate_test_data",
                    payload={"schema": schema, "count": count},
                    priority=2,
                )
                
                task_id = coordinator.submit_task(task)
                st.info(f"📋 Task submitted: {task_id}")
                
                # Wait for result
                start_time = time.time()
                while time.time() - start_time < 30:
                    result = coordinator.task_results.get(task_id)
                    if result:
                        if result.status == TaskStatus.COMPLETED:
                            df_data = pd.DataFrame(result.result)
                            st.subheader("Generated Data")
                            st.dataframe(df_data, use_container_width=True)
                            
                            # Download
                            buffer = BytesIO()
                            df_data.to_excel(buffer, index=False, engine="openpyxl")
                            buffer.seek(0)
                            
                            st.download_button(
                                "📥 Download Data as Excel",
                                data=buffer,
                                file_name="generated_data.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            break
                        elif result.status == TaskStatus.FAILED:
                            st.error(f"Task failed: {result.error}")
                            break
                    
                    time.sleep(0.5)
                else:
                    st.warning("Task still processing, check dashboard")
        
        else:
            st.warning("Please describe the data you need.")


# =========================================================
# PAGE 5 — LOCATOR REPAIR
# =========================================================
elif page == "🔧 Locator Repair":
    st.header("🔧 Self-Healing Locator Repair")
    
    xpath_input = st.text_input("Enter XPath that failed", "//*[@id='username']")
    error_msg = st.text_area("Enter error message", "Element not found")
    
    if st.button("🔍 Find Alternative Locators"):
        with st.spinner("Analyzing and finding alternatives..."):
            
            task = TaskMessage(
                agent_type=AgentType.LOCATOR_REPAIR,
                action="repair_xpath",
                payload={
                    "original_xpath": xpath_input,
                    "dom_snapshot": "",
                    "error": error_msg,
                },
                priority=2,
            )
            
            task_id = coordinator.submit_task(task)
            
            # Wait for result
            start_time = time.time()
            while time.time() - start_time < 30:
                result = coordinator.task_results.get(task_id)
                if result and result.status == TaskStatus.COMPLETED:
                    st.success("✅ Suggestions found!")
                    
                    if result.result.get("suggestions"):
                        for idx, sugg in enumerate(result.result["suggestions"], 1):
                            st.code(sugg["xpath"], language="xpath")
                            st.caption(f"Strategy: {sugg['strategy']} | Confidence: {sugg['confidence']:.0%}")
                            st.divider()
                    break
                
                time.sleep(0.5)


# =========================================================
# PAGE 6 — DATA VALIDATION
# =========================================================
elif page == "✓ Data Validation":
    st.header("✓ Data Quality Validation")
    
    uploaded_file = st.file_uploader("Upload test data file", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        data = df.to_dict(orient="records")
        
        if st.button("🔍 Validate Data"):
            with st.spinner("Validating data quality..."):
                
                # Check for duplicates
                task1 = TaskMessage(
                    agent_type=AgentType.DATA_VALIDATOR,
                    action="detect_duplicates",
                    payload={"data": data},
                    priority=2,
                )
                
                # Validate data
                task2 = TaskMessage(
                    agent_type=AgentType.DATA_VALIDATOR,
                    action="validate_test_data",
                    payload={"data": data},
                    priority=2,
                )
                
                task1_id = coordinator.submit_task(task1)
                task2_id = coordinator.submit_task(task2)
                
                st.info(f"📋 Submitted 2 validation tasks")
                
                # Wait for both results
                results_found = 0
                start_time = time.time()
                while time.time() - start_time < 30 and results_found < 2:
                    r1 = coordinator.task_results.get(task1_id)
                    r2 = coordinator.task_results.get(task2_id)
                    
                    if r1 and r1.status == TaskStatus.COMPLETED:
                        st.subheader("Duplicate Analysis")
                        st.json(r1.result)
                        results_found += 1
                    
                    if r2 and r2.status == TaskStatus.COMPLETED:
                        st.subheader("Data Quality Report")
                        st.json(r2.result)
                        results_found += 1
                    
                    time.sleep(0.5)


# =========================================================
# PAGE 7 — PERFORMANCE ANALYSIS
# =========================================================
elif page == "⏱️ Performance Analysis":
    st.header("⏱️ Test Performance Analysis")
    
    st.info("This analyzes performance from completed test runs. Run tests first, then check back.")
    
    workflow_id = st.text_input("Enter Workflow ID to analyze", "")
    
    if workflow_id:
        workflow_status = coordinator.get_workflow_status(workflow_id)
        
        if workflow_status:
            st.success(f"✅ Found workflow: {workflow_id}")
            
            # Extract test results from first task
            if workflow_status.get("task_results"):
                first_result = workflow_status["task_results"][0]
                
                if first_result.get("result"):
                    test_results = first_result["result"]
                    
                    # Create performance analysis task
                    task = TaskMessage(
                        agent_type=AgentType.PERFORMANCE_ANALYZER,
                        action="analyze_test_performance",
                        payload={"test_results": test_results},
                        priority=2,
                    )
                    
                    task_id = coordinator.submit_task(task)
                    
                    # Also create bottleneck analysis
                    task2 = TaskMessage(
                        agent_type=AgentType.PERFORMANCE_ANALYZER,
                        action="identify_bottlenecks",
                        payload={"test_results": test_results, "threshold_ms": 1000},
                        priority=2,
                    )
                    
                    task2_id = coordinator.submit_task(task2)
                    
                    st.info("📊 Analyzing performance metrics...")
                    
                    # Wait for results
                    start_time = time.time()
                    while time.time() - start_time < 30:
                        r1 = coordinator.task_results.get(task_id)
                        r2 = coordinator.task_results.get(task2_id)
                        
                        if r1 and r1.status == TaskStatus.COMPLETED:
                            st.subheader("Performance Metrics")
                            st.json(r1.result)
                        
                        if r2 and r2.status == TaskStatus.COMPLETED:
                            st.subheader("Bottleneck Analysis")
                            st.json(r2.result)
                            break
                        
                        time.sleep(0.5)
        else:
            st.warning(f"Workflow {workflow_id} not found")


# =========================================================
# FOOTER
# =========================================================
st.divider()
st.caption("🤖 Multi-Agent Test Automation Framework | Powered by Coordinator Agent")
