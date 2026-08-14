# =========================================================
# TEST EXECUTOR AGENT - Runs UI & API tests
# =========================================================

from typing import Any, Dict, List
from datetime import datetime
import time
import traceback

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException

from agents.agent_base import Agent, AgentType, TaskMessage, TaskResult, TaskStatus
from core.keyword_engine import KEYWORD_MAP


class TestExecutorAgent(Agent):
    """
    Executes test cases from Excel files.
    
    Actions:
    - run_test_cases: Execute list of test steps
    - run_data_driven_test: Execute with multiple data sets
    """
    
    def __init__(self):
        super().__init__(AgentType.TEST_EXECUTOR, "Test Executor")
        self.driver = None
        self.screenshots = []
        
    def execute(self, task: TaskMessage) -> TaskResult:
        """Execute test task"""
        
        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
        )
        
        try:
            if task.action == "run_test_cases":
                result.result = self._run_test_cases(
                    task.payload.get("test_steps", []),
                    task.payload.get("data_row", {}),
                    task.payload.get("env", "DEV")
                )
                
            elif task.action == "run_data_driven_test":
                result.result = self._run_data_driven_test(
                    task.payload.get("test_steps", []),
                    task.payload.get("data_rows", []),
                    task.payload.get("env", "DEV")
                )
                
            else:
                raise ValueError(f"Unknown action: {task.action}")
            
            result.status = TaskStatus.COMPLETED
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.metadata["traceback"] = traceback.format_exc()
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
        
        return result
    
    def _run_test_cases(
        self,
        test_steps: List[Dict[str, Any]],
        data_row: Dict[str, str] = None,
        env: str = "DEV"
    ) -> Dict[str, Any]:
        """
        Execute a single test with optional data row.
        
        Returns:
            Test execution summary
        """
        if data_row is None:
            data_row = {}
        
        # Initialize browser
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        
        step_results = []
        passed = 0
        failed = 0
        
        print(f"🧪 Starting test run with {len(test_steps)} steps (env: {env})")
        
        for idx, step in enumerate(test_steps, 1):
            step_result = {
                "step_num": idx,
                "description": step.get("Description", ""),
                "action": step.get("Action", ""),
                "status": "PASS",
                "error": "",
                "duration_ms": 0,
            }
            
            start_time = time.time()
            
            try:
                # Substitute placeholders
                xpath = self._substitute_placeholders(step.get("XPath", "N/A"), data_row)
                action = str(step.get("Action", "")).strip()
                data = self._substitute_placeholders(step.get("Data", ""), data_row)
                
                # Execute keyword
                if action not in KEYWORD_MAP:
                    raise Exception(f"Unknown action: {action}")
                
                KEYWORD_MAP[action](
                    self.driver,
                    xpath if xpath != "N/A" else None,
                    data
                )
                
                time.sleep(0.3)  # Small delay for UI rendering
                passed += 1
                
            except Exception as e:
                step_result["status"] = "FAIL"
                step_result["error"] = str(e)
                failed += 1
                print(f"  ❌ Step {idx} failed: {e}")
            
            step_result["duration_ms"] = int((time.time() - start_time) * 1000)
            step_results.append(step_result)
        
        duration_sec = time.time()
        
        summary = {
            "total_steps": len(test_steps),
            "passed_steps": passed,
            "failed_steps": failed,
            "success_rate": (passed / len(test_steps) * 100) if test_steps else 0,
            "steps": step_results,
            "environment": env,
            "duration_sec": duration_sec,
            "screenshots": self.screenshots,
        }
        
        print(f"✅ Test run completed: {passed}/{len(test_steps)} steps passed")
        return summary
    
    def _run_data_driven_test(
        self,
        test_steps: List[Dict[str, Any]],
        data_rows: List[Dict[str, str]],
        env: str = "DEV"
    ) -> Dict[str, Any]:
        """
        Execute test with multiple data rows (data-driven testing).
        
        Returns:
            Aggregated results for all data iterations
        """
        results = []
        total_passed = 0
        total_failed = 0
        
        print(f"🔄 Running data-driven test with {len(data_rows)} data sets")
        
        for data_idx, data_row in enumerate(data_rows, 1):
            print(f"  📊 Data iteration {data_idx}/{len(data_rows)}")
            
            result = self._run_test_cases(test_steps, data_row, env)
            result["data_row_num"] = data_idx
            result["data"] = data_row
            
            results.append(result)
            total_passed += result["passed_steps"]
            total_failed += result["failed_steps"]
        
        return {
            "test_type": "data_driven",
            "total_data_rows": len(data_rows),
            "total_steps_per_row": len(test_steps),
            "total_steps_executed": len(data_rows) * len(test_steps),
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_success_rate": (
                total_passed / (len(data_rows) * len(test_steps)) * 100
                if data_rows and test_steps else 0
            ),
            "iterations": results,
            "environment": env,
        }
    
    def _substitute_placeholders(self, value: str, data_row: Dict[str, str]) -> str:
        """Replace {{key}} placeholders with data_row values"""
        if not isinstance(value, str):
            return value
        
        for key, val in data_row.items():
            placeholder = f"{{{{{key}}}}}"
            value = value.replace(placeholder, str(val))
        
        return value
