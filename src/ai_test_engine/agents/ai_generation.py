"""
The AI Generation agent: the LLM-backed half of the framework.

Turns plain-English intent into structured test artifacts:
    generate_test_from_description - "log in as admin" -> executable steps
    generate_test_data             - synthetic rows for data-driven runs
    optimize_test_suite            - suggestions across many runs
    suggest_fix_for_failure        - remediation advice for a failed step

Provider is chosen via the ``llm_provider`` argument (settings.AI_PROVIDER):
    "stub"   - canned offline responses; no API key, no network. The default,
               so the project works on a fresh clone.
    "openai" - OpenAI, reads OPENAI_API_KEY
    "claude" - Anthropic, reads ANTHROPIC_API_KEY

If the selected provider's SDK isn't installed the agent falls back to "stub"
rather than failing. Model replies are parsed by ``_parse_steps``, which also
falls back to the stub if the reply isn't usable JSON -- a bad LLM response
degrades the run, it never crashes it.
"""

# =========================================================
# AI GENERATION AGENT - Generates tests, data, and suggestions
# =========================================================

from typing import Any, Dict, List
import json
import traceback

from ai_test_engine.agents.agent_base import Agent, AgentType, TaskMessage, TaskResult, TaskStatus
from ai_test_engine.core.keyword_engine import KEYWORD_MAP
from ai_test_engine.prompts import GENERATE_TEST_STEPS

# Public practice site used by the offline stub and the sample workbooks, so
# the demo runs green out of the box with no client system involved.
LOGIN_DEMO_URL = "https://practicetestautomation.com/practice-test-login/"
LOGIN_DEMO_CREDENTIALS = {"username": "student", "password": "Password123"}


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
        """Return canned steps that actually execute successfully.

        Targets practicetestautomation.com -- the same public practice site the
        sample workbooks use -- rather than example.com, which has no login
        form. That matters: these steps are what the offline demo runs, so
        pointing them at a page with no matching elements made every demo run
        fail, and (with an implicit wait configured) fail slowly.
        """
        print(f"🤖 (Stub) Generating test for: {description}")
        return [
            {"Description": "Open login page", "XPath": "N/A", "Action": "launch_url", "Data": LOGIN_DEMO_URL},
            {"Description": "Enter username", "XPath": "//*[@id='username']", "Action": "enter_text", "Data": "{{username}}"},
            {"Description": "Enter password", "XPath": "//*[@id='password']", "Action": "enter_text", "Data": "{{password}}"},
            {"Description": "Click login button", "XPath": "//*[@id='submit']", "Action": "click", "Data": ""},
            {"Description": "Verify login succeeded", "XPath": "//h1", "Action": "verify_text", "Data": "Logged In Successfully"},
        ]
    
    def _generate_test_openai(self, description: str) -> List[Dict[str, str]]:
        """Use OpenAI GPT to generate tests. Requires OPENAI_API_KEY."""
        prompt = GENERATE_TEST_STEPS.format(
            description=description, actions=", ".join(KEYWORD_MAP)
        )

        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )

        print(f"🤖 (OpenAI) Generated test steps")
        return self._parse_steps(
            response.choices[0].message.content, description
        )
    
    def _generate_test_claude(self, description: str) -> List[Dict[str, str]]:
        """Use Claude to generate tests. Requires ANTHROPIC_API_KEY."""
        prompt = GENERATE_TEST_STEPS.format(
            description=description, actions=", ".join(KEYWORD_MAP)
        )

        message = self.llm_client.messages.create(
            model="claude-opus-5",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
        )

        print(f"🤖 (Claude) Generated test steps")
        text = next((b.text for b in message.content if b.type == "text"), "")
        return self._parse_steps(text, description)

    def _parse_steps(self, text: str, description: str) -> List[Dict[str, str]]:
        """Extract the JSON array of steps from an LLM reply.

        Falls back to the stub if the model wrapped the array in prose or
        returned something unparseable, so a bad reply never breaks a run.
        """
        if text:
            start, end = text.find("["), text.rfind("]")
            if start != -1 and end > start:
                try:
                    steps = json.loads(text[start:end + 1])
                    if isinstance(steps, list) and steps:
                        return steps
                except json.JSONDecodeError:
                    pass

        print("⚠️ Could not parse LLM response, falling back to stub")
        return self._generate_test_stub(description)
    
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
            # Credentials the demo login page actually accepts. Invented ones
            # ("user1"/"Pass101!") make every generated login test fail, which
            # looks like a framework bug rather than intentional sample data.
            return [
                {**LOGIN_DEMO_CREDENTIALS, "email": f"user{i}@test.com"}
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
