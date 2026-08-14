"""
LLM helper functions used by the single-agent runner.

**These are all stubs.** Each returns a canned, deterministic response so the
framework runs end-to-end with no API key and no network. Replace the bodies
with real LLM calls to activate the AI behaviour -- the call sites already
expect the shapes returned here.

    ai_generate_test_from_description - natural language -> test steps
    ai_explain_failure                - readable diagnosis of a failed step
    ai_suggest_locator_repair         - replacement XPath for a stale locator
                                        (returning it unchanged is why
                                        self-healing is currently inert)
    ai_optimize_test_suite            - suite-level improvement suggestions
    ai_generate_test_data             - synthetic data rows

The multi-agent equivalent is agents/ai_generation.py, which does support
real providers.
"""

# =========================================================
# AI ENGINE MODULE
# =========================================================

def ai_generate_test_from_description(description: str):
    """
    Convert natural language into structured test steps.
    Replace this stub with a real LLM call later.
    """
    return [
        {
            "Description": "Open login page",
            "XPath": "N/A",
            "Action": "launch_url",
            "Data": "https://example.com/login",
        },
        {
            "Description": "Enter username",
            "XPath": "//*[@id='username']",
            "Action": "enter_text",
            "Data": "test_user",
        },
        {
            "Description": "Enter password",
            "XPath": "//*[@id='password']",
            "Action": "enter_text",
            "Data": "Password123",
        },
        {
            "Description": "Click login",
            "XPath": "//*[@id='submit']",
            "Action": "click",
            "Data": "",
        },
    ]


def ai_explain_failure(step, error: str):
    """
    Provide a human-readable explanation for a failed step.
    """
    return (
        f"Step '{step['Description']}' failed.\n"
        f"Action: {step['Action']}\n"
        f"Likely cause: {error}\n"
        f"Suggestion: Verify locator '{step['XPath']}' and data '{step['Data']}'."
    )


def ai_suggest_locator_repair(xpath: str, dom_snapshot: str):
    """
    Suggest a repaired locator based on DOM.
    Replace with real LLM logic later.
    """
    return xpath  # Stub: return original until AI is wired in


def ai_optimize_test_suite(test_summaries):
    """
    Suggest improvements for a suite of tests.
    """
    return (
        "AI Optimization Suggestions:\n"
        "- Merge duplicate login tests.\n"
        "- Parameterize repeated flows.\n"
        "- Add negative scenarios.\n"
        "- Remove redundant navigation steps."
    )


def ai_generate_test_data(schema_description: str):
    """
    Generate synthetic test data based on a schema description.
    """
    return [
        {"username": "user1", "password": "Password123"},
        {"username": "user2", "password": "Password456"},
    ]
