# =========================================================
# SPECIALIZED AGENTS - Locator Repair, Data Validator, Perf Analyzer
# =========================================================

from typing import Any, Dict, List
import traceback
import re

from agents.agent_base import Agent, AgentType, TaskMessage, TaskResult, TaskStatus


class LocatorRepairAgent(Agent):
    """
    Self-healing locator recovery.
    
    Actions:
    - repair_xpath: Suggest fixes for broken XPath
    - find_alternative_locator: Use ML/heuristics to find element
    """
    
    def __init__(self):
        super().__init__(AgentType.LOCATOR_REPAIR, "Locator Repair")
    
    def execute(self, task: TaskMessage) -> TaskResult:
        """Execute locator repair task"""
        
        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
        )
        
        try:
            if task.action == "repair_xpath":
                result.result = self.repair_xpath(
                    task.payload.get("original_xpath", ""),
                    task.payload.get("dom_snapshot", ""),
                    task.payload.get("error", "")
                )
                
            elif task.action == "find_alternative_locator":
                result.result = self.find_alternative_locator(
                    task.payload.get("element_description", ""),
                    task.payload.get("dom_snapshot", "")
                )
                
            else:
                raise ValueError(f"Unknown action: {task.action}")
            
            result.status = TaskStatus.COMPLETED
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.metadata["traceback"] = traceback.format_exc()
        
        return result
    
    def repair_xpath(
        self,
        original_xpath: str,
        dom_snapshot: str,
        error: str
    ) -> Dict[str, Any]:
        """
        Suggest repairs for broken XPath locators.
        
        Strategies:
        - Convert @id to @name if element still exists
        - Relax attribute matching
        - Use text-based locators
        - Try parent/sibling navigation
        """
        
        print(f"🔧 Repairing XPath: {original_xpath}")
        
        suggestions = []
        
        # Strategy 1: Replace @id with @name
        if "@id=" in original_xpath:
            repaired = original_xpath.replace("@id=", "@name=")
            suggestions.append({
                "xpath": repaired,
                "strategy": "Replace @id with @name",
                "confidence": 0.6,
            })
        
        # Strategy 2: Remove attributes and use text matching
        if "text()" not in original_xpath:
            text_based = original_xpath.split("[")[0] + "[contains(text(), 'search_text')]"
            suggestions.append({
                "xpath": text_based,
                "strategy": "Use text-based matching",
                "confidence": 0.5,
            })
        
        # Strategy 3: Use class or aria-label
        if "class=" not in original_xpath:
            class_based = original_xpath.replace("//*", "//*[@class]")
            suggestions.append({
                "xpath": class_based,
                "strategy": "Match by class attribute",
                "confidence": 0.4,
            })
        
        return {
            "original_xpath": original_xpath,
            "error": error,
            "suggestions": suggestions,
            "recommended": suggestions[0] if suggestions else None,
            "self_heal_confidence": max([s["confidence"] for s in suggestions], default=0),
        }
    
    def find_alternative_locator(
        self,
        element_description: str,
        dom_snapshot: str
    ) -> Dict[str, Any]:
        """
        Find alternative locators for an element.
        
        Example:
            Input: "Login button on the top right"
            Output: [
                {"locator": "//*[@id='login-btn']", "type": "id", "strength": 0.95},
                {"locator": "//button[text()='Login']", "type": "text", "strength": 0.85},
                {"locator": "//button.primary", "type": "class", "strength": 0.75},
            ]
        """
        
        print(f"🔍 Finding alternative locators for: {element_description}")
        
        # Mock implementation - would use ML in production
        return {
            "element_description": element_description,
            "locators": [
                {
                    "locator": "//*[@id='login']",
                    "type": "id",
                    "strength": 0.95,
                    "description": "Exact ID match",
                },
                {
                    "locator": "//button[contains(text(), 'Login')]",
                    "type": "text",
                    "strength": 0.80,
                    "description": "Button by text content",
                },
                {
                    "locator": "//button.btn-primary",
                    "type": "class",
                    "strength": 0.70,
                    "description": "Button by CSS class",
                },
            ],
            "recommended_locator": "//*[@id='login']",
        }


class DataValidatorAgent(Agent):
    """
    Validates test data quality and consistency.
    
    Actions:
    - validate_test_data: Check data format and values
    - detect_duplicates: Find duplicate records
    - validate_schema: Verify data matches expected schema
    """
    
    def __init__(self):
        super().__init__(AgentType.DATA_VALIDATOR, "Data Validator")
    
    def execute(self, task: TaskMessage) -> TaskResult:
        """Execute data validation task"""
        
        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
        )
        
        try:
            if task.action == "validate_test_data":
                result.result = self.validate_test_data(
                    task.payload.get("data", []),
                    task.payload.get("schema", {})
                )
                
            elif task.action == "detect_duplicates":
                result.result = self.detect_duplicates(
                    task.payload.get("data", [])
                )
                
            elif task.action == "validate_schema":
                result.result = self.validate_schema(
                    task.payload.get("data", []),
                    task.payload.get("expected_schema", {})
                )
                
            else:
                raise ValueError(f"Unknown action: {task.action}")
            
            result.status = TaskStatus.COMPLETED
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.metadata["traceback"] = traceback.format_exc()
        
        return result
    
    def validate_test_data(
        self,
        data: List[Dict[str, Any]],
        schema: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate test data for format, types, and business rules.
        """
        
        print(f"✓ Validating {len(data)} data records")
        
        issues = []
        warnings = []
        
        for idx, record in enumerate(data):
            # Check for required fields
            if schema:
                for field, field_type in schema.items():
                    if field not in record:
                        issues.append(f"Record {idx}: Missing required field '{field}'")
            
            # Check for empty values
            for key, value in record.items():
                if value is None or str(value).strip() == "":
                    warnings.append(f"Record {idx}: Field '{key}' is empty")
        
        return {
            "total_records": len(data),
            "valid_records": len(data) - len(issues),
            "issues": issues,
            "warnings": warnings,
            "is_valid": len(issues) == 0,
            "quality_score": max(0, (len(data) - len(issues)) / len(data)) if data else 0,
        }
    
    def detect_duplicates(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find duplicate records in test data.
        """
        
        print(f"🔍 Detecting duplicates in {len(data)} records")
        
        seen = {}
        duplicates = []
        
        for idx, record in enumerate(data):
            # Create a hashable representation
            record_hash = tuple(sorted(record.items()))
            
            if record_hash in seen:
                duplicates.append({
                    "current_index": idx,
                    "duplicate_of_index": seen[record_hash],
                    "record": record,
                })
            else:
                seen[record_hash] = idx
        
        return {
            "total_records": len(data),
            "duplicate_count": len(duplicates),
            "duplicates": duplicates,
            "deduplication_needed": len(duplicates) > 0,
            "deduplication_ratio": len(duplicates) / len(data) if data else 0,
        }
    
    def validate_schema(
        self,
        data: List[Dict[str, Any]],
        expected_schema: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Verify data matches expected schema (fields and types).
        """
        
        print(f"📋 Validating schema for {len(data)} records")
        
        errors = []
        
        for idx, record in enumerate(data):
            for field, expected_type in expected_schema.items():
                if field not in record:
                    errors.append(f"Record {idx}: Missing field '{field}'")
                else:
                    value = record[field]
                    # Simple type checking
                    if expected_type == "string" and not isinstance(value, str):
                        errors.append(f"Record {idx}: Field '{field}' should be string, got {type(value).__name__}")
                    elif expected_type == "int" and not isinstance(value, int):
                        errors.append(f"Record {idx}: Field '{field}' should be int, got {type(value).__name__}")
        
        return {
            "total_records": len(data),
            "schema_matches": len(data) - len(errors),
            "errors": errors,
            "is_valid": len(errors) == 0,
            "expected_schema": expected_schema,
        }


class PerformanceAnalyzerAgent(Agent):
    """
    Analyzes test execution performance and bottlenecks.
    
    Actions:
    - analyze_test_performance: Extract metrics from test run
    - identify_bottlenecks: Find slow steps
    - generate_performance_report: Create performance summary
    """
    
    def __init__(self):
        super().__init__(AgentType.PERFORMANCE_ANALYZER, "Performance Analyzer")
    
    def execute(self, task: TaskMessage) -> TaskResult:
        """Execute performance analysis task"""
        
        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
        )
        
        try:
            if task.action == "analyze_test_performance":
                result.result = self.analyze_test_performance(
                    task.payload.get("test_results", {})
                )
                
            elif task.action == "identify_bottlenecks":
                result.result = self.identify_bottlenecks(
                    task.payload.get("test_results", {}),
                    task.payload.get("threshold_ms", 1000)
                )
                
            elif task.action == "generate_performance_report":
                result.result = self.generate_performance_report(
                    task.payload.get("test_results", {})
                )
                
            else:
                raise ValueError(f"Unknown action: {task.action}")
            
            result.status = TaskStatus.COMPLETED
            
        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            result.metadata["traceback"] = traceback.format_exc()
        
        return result
    
    def analyze_test_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key performance metrics from test execution.
        """
        
        print(f"⏱️ Analyzing test performance")
        
        steps = test_results.get("steps", [])
        durations = [s.get("duration_ms", 0) for s in steps]
        
        if not durations:
            return {"error": "No step duration data"}
        
        total_duration = sum(durations)
        avg_duration = total_duration / len(durations)
        max_duration = max(durations)
        min_duration = min(durations)
        
        return {
            "total_duration_ms": total_duration,
            "total_duration_sec": total_duration / 1000,
            "avg_step_duration_ms": avg_duration,
            "max_step_duration_ms": max_duration,
            "min_step_duration_ms": min_duration,
            "total_steps": len(steps),
            "throughput_steps_per_sec": len(steps) / (total_duration / 1000) if total_duration > 0 else 0,
        }
    
    def identify_bottlenecks(
        self,
        test_results: Dict[str, Any],
        threshold_ms: int = 1000
    ) -> Dict[str, Any]:
        """
        Find slow steps that exceed threshold.
        """
        
        print(f"🔍 Identifying bottlenecks (threshold: {threshold_ms}ms)")
        
        steps = test_results.get("steps", [])
        bottlenecks = [
            {
                "step_num": s["step_num"],
                "description": s.get("description", ""),
                "action": s.get("action", ""),
                "duration_ms": s.get("duration_ms", 0),
                "excess_ms": s.get("duration_ms", 0) - threshold_ms,
            }
            for s in steps
            if s.get("duration_ms", 0) > threshold_ms
        ]
        
        return {
            "threshold_ms": threshold_ms,
            "bottleneck_count": len(bottlenecks),
            "bottlenecks": sorted(bottlenecks, key=lambda x: x["duration_ms"], reverse=True),
            "optimization_potential": sum(b["excess_ms"] for b in bottlenecks),
        }
    
    def generate_performance_report(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        """
        
        perf_analysis = self.analyze_test_performance(test_results)
        bottlenecks = self.identify_bottlenecks(test_results, 1000)
        
        return {
            "performance_summary": perf_analysis,
            "bottlenecks": bottlenecks,
            "recommendations": [
                "Parallelize independent test steps where possible",
                f"Optimize the {len(bottlenecks)} slow steps identified",
                "Consider caching static data to reduce setup time",
                "Implement headless browser mode for faster UI automation",
                "Use explicit waits instead of sleep() for better performance",
            ],
            "generated_at": str(__import__('datetime').datetime.now()),
        }
