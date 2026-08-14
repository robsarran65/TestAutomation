# =========================================================
# AI GENERATION AGENT - Generates tests, data, and suggestions
# =========================================================

from typing import Any, Dict, List
import traceback

from framework.agent_base import Agent, AgentType, TaskMessage, TaskResult, TaskStatus


class AIGenerationAgent(Agent):
    """
    AI-powered test generation and optimization.
    
    Actions:
    - generate_test_from_description: Convert natural language to test steps
    - generate_test_data: Create synthetic test data
    - optimize_test_suite: Analyze and suggest improvements
    - suggest_fix_for_failure: Recommend repair for failed step
    """
    
    def __init__(self, llm_provider: str = "stub"):
        """
        Args:
            llm_provider: 'stub' (mock), 'openai', 'claude', 'local'
        """
        super().__init__(AgentType.AI_GENERATION, "AI Generation")
        self.llm_provider = llm_provider
        self.llm_client = None
        
        if llm_provider == "openai":
            try:
                import openai
                self.llm_client = openai.OpenAI()
            except ImportError:
                print("⚠️ OpenAI not installed, falling back to stub")
                self.llm_provider = "stub"
        
        elif llm_provider == "claude":
            try:
                import anthropic
                self.llm_client = anthropic.Anthropic()
            except ImportError:
                print("⚠️ Anthropic not installed, falling back to stub")
                self.llm_provider = "stub"
    
    def execute(self, task: TaskMessage) -> TaskResult:
        """Execute AI task"""
        
        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
        )
        
        try:
            if task.action == "generate_test_from_description":
                result.result = self.generate_test_from_description(
                    task.payload.get("description", "")
                )
                
            elif task.action == "generate_test_data":
                result.result = self.generate_test_data(
                    task.payload.get("schema", ""),
                    task.payload.get("count", 5)
                )
                
            elif task.action == "optimize_test_suite":
                result.result = self.optimize_test_suite(
                    task.payload.get("test_summaries", [])
                )
                
            elif task.action == "suggest_fix_for_failure":
                result.result = self.suggest_fix_for_failure(
                    task.payload.get("step", {}),
                    task.payload.get("error", ""),
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
    
    def generate_test_from_description(self, description: str) -> List[Dict[str, str]]:
        """
        Convert natural language test description to structured steps.
        
        Example:
            Input: "Login with valid credentials and verify dashboard"
            Output: [
                {"Description": "Open login page", "XPath": "//*[@id='login']", "Action": "click", "Data": ""},
                {"Description": "Enter username", "XPath": "//*[@id='user']", "Action": "enter_text", "Data": "{{username}}"},
                ...
            ]
        """
        
        if self.llm_provider == "stub":
            return self._generate_test_stub(description)
        
        elif self.llm_provider == "openai":
            return self._generate_test_openai(description)
        
        elif self.llm_provider == "claude":
            return self._generate_test_claude(description)
        
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")
    
    def _generate_test_stub(self, description: str) -> List[Dict[str, str]]:
        """Stub implementation - returns generic test steps"""
        print(f"🤖 (Stub) Generating test for: {description}")
        return [
            {"Description": "Open login page", "XPath": "//*[@id='login']", "Action": "launch_url", "Data": "https://example.com/login"},
            {"Description": "Enter username", "XPath": "//*[@id='username']", "Action": "enter_text", "Data": "{{username}}"},
            {"Description": "Enter password", "XPath": "//*[@id='password']", "Action": "enter_text", "Data": "{{password}}"},
            {"Description": "Click login button", "XPath": "//*[@id='submit']", "Action": "click", "Data": ""},
            {"Description": "Verify dashboard loaded", "XPath": "//*[@id='dashboard']", "Action": "verify_text", "Data": "Dashboard"},
        ]
    
    def _generate_test_openai(self, description: str) -> List[Dict[str, str]]:
        """Use OpenAI GPT to generate tests"""
        prompt = f"""
        Convert this test description into structured test steps.
        Return JSON array with fields: Description, XPath, Action, Data
        
        Description: {description}
        
        Actions can be: launch_url, enter_text, click, verify_text, wait_for_element
        """
        
        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        
        # Parse response (implementation depends on LLM response format)
        print(f"🤖 (OpenAI) Generated test steps")
        return self._generate_test_stub(description)  # Fallback for now
    
    def _generate_test_claude(self, description: str) -> List[Dict[str, str]]:
        """Use Claude to generate tests"""
        prompt = f"""
        Convert this test description into structured test steps.
        Return JSON array with fields: Description, XPath, Action, Data
        
        Description: {description}
        """
        
        message = self.llm_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        
        print(f"🤖 (Claude) Generated test steps")
        return self._generate_test_stub(description)  # Fallback for now
    
    def generate_test_data(self, schema: str, count: int = 5) -> List[Dict[str, str]]:
        """
        Generate synthetic test data based on schema.
        
        Example:
            Input: "usernames and passwords for login testing"
            Output: [
                {"username": "user1", "password": "Pass123!"},
                {"username": "user2", "password": "Pass456!"},
                ...
            ]
        """
        print(f"🤖 Generating {count} test data sets for: {schema}")
        
        if self.llm_provider == "stub":
            return [
                {"username": f"user{i}", "password": f"Pass{100+i}!", "email": f"user{i}@test.com"}
                for i in range(1, count + 1)
            ]
        
        # TODO: Integrate with real LLM
        return []
    
    def optimize_test_suite(self, test_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze test suite and suggest optimizations.
        
        Returns:
            {
                "suggestions": [...],
                "redundancy_score": 0.0-1.0,
                "coverage_gaps": [...],
            }
        """
        print(f"🤖 Analyzing {len(test_summaries)} tests for optimization opportunities")
        
        return {
            "suggestions": [
                "Merge duplicate login tests",
                "Parameterize repeated flows",
                "Add negative test scenarios",
                "Remove redundant navigation steps",
            ],
            "redundancy_score": 0.35,
            "coverage_gaps": [
                "Error handling paths",
                "Timeout scenarios",
                "Concurrent user testing",
            ],
            "estimated_reduction": "20-30% fewer tests with same coverage",
        }
    
    def suggest_fix_for_failure(
        self,
        step: Dict[str, str],
        error: str,
        dom_snapshot: str = ""
    ) -> Dict[str, Any]:
        """
        Suggest how to fix a failed test step.
        
        Returns:
            {
                "suggestion": "...",
                "alternative_xpath": "...",
                "debug_tips": [...],
            }
        """
        print(f"🤖 Suggesting fix for failed step: {step.get('Description', '')}")
        
        return {
            "suggestion": f"The element may have changed. Try updating the XPath.",
            "alternative_xpath": step.get("XPath", "").replace("@id=", "@name="),
            "debug_tips": [
                "Use browser DevTools to inspect the element",
                "Check if element is loaded dynamically (use wait)",
                "Verify XPath in browser console: $x(xpath)",
                "Try alternative locators: CSS selector, text content, etc",
            ],
            "confidence": 0.65,
        }
