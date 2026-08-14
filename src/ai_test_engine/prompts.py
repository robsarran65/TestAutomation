"""
Prompt templates for the AI agents.

Prompts are kept here, out of the agent code, because they are tuned far more
often than the logic around them. Centralising them means you can review or
diff a wording change without reading through client setup and parsing code,
and the same prompt text is shared across providers.

Each template is a ``str.format`` string -- fill it with ``.format(...)``.
Keep the "return JSON array" instruction intact: ``_parse_steps`` in
agents/ai_generation.py depends on the model replying with a JSON array, and
falls back to canned steps when it doesn't.
"""

# Natural language -> executable test steps.
# ACTIONS must stay in sync with KEYWORD_MAP in core/keyword_engine.py; naming
# an action the engine doesn't know fails the step at runtime.
GENERATE_TEST_STEPS = """\
Convert this test description into structured test steps.
Return a JSON array where each element has exactly these fields:
Description, XPath, Action, Data

Valid values for Action: {actions}

Description: {description}

Return only the JSON array, no commentary.
"""

# Synthetic rows for data-driven runs.
GENERATE_TEST_DATA = """\
Generate {count} rows of realistic test data for: {schema}

Return a JSON array of objects that all share the same keys.
Return only the JSON array, no commentary.
"""

# Remediation advice for a step that failed.
SUGGEST_FIX = """\
A test step failed. Suggest the most likely cause and a concrete fix.

Step:  {step}
Error: {error}

Be specific about which locator or data value to change.
"""
