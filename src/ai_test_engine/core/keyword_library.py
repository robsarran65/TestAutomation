"""
Reference list of the keywords available in a test workbook's Action column.

Documentation only -- the executable dispatch table is KEYWORD_MAP in
keyword_engine.py. Keep the two in sync when adding a keyword.
"""

KEYWORDS = [
    ("launch_url", "Open browser and navigate to URL"),
    ("enter_text", "Enter text into a field"),
    ("click", "Click an element"),
    ("verify_text", "Verify element text"),

    # Future keywords
    ("wait_for_element", "Wait until element is visible"),
    ("verify_element_present", "Check element exists"),
    ("select_dropdown_by_text", "Select dropdown option by text"),
    ("hover", "Hover over an element"),
    ("screenshot", "Capture screenshot"),
    ("run_sql_query", "Execute DB query and validate"),
    ("load_data_from_sheet", "Use external data source"),
    ("loop_over_data_set", "Run test for multiple data rows"),
    ("close_app", "Close browser"),
]
