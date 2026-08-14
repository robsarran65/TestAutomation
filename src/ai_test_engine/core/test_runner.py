"""
Single-agent test runner: the engine behind the classic (non-multi-agent) UI.

Reads an Excel workbook where each row is one test step, drives a real Chrome
browser through those steps, and emits an HTML report, a PDF report, and a
pass/fail pie chart into ``outputs/reports/``.

Expected workbook columns:
    Description | XPath | Action | Data

``Action`` must name a keyword in ``KEYWORD_MAP`` (see keyword_engine.py).
A workbook whose ``Action`` column is entirely empty is treated as a *data*
file for data-driven runs rather than a test file.

The multi-agent equivalent of this module is agents/executor.py.
"""

import re
import time
import pandas as pd
from selenium.common.exceptions import WebDriverException
from ai_test_engine.core.browser import create_driver
from ai_test_engine.core.keyword_engine import KEYWORD_MAP, requires_browser
from ai_test_engine.core.ai_engine import ai_explain_failure
from ai_test_engine.config.settings import REPORTS_DIR, TEST_DATA_DIR
from fpdf import FPDF
import os
import matplotlib.pyplot as plt


# =========================================================
# Helper: Substitute {{placeholders}} with data row values
# =========================================================
def substitute_placeholders(value, data_row):
    """Expand ``{{key}}`` tokens in a cell using one row of test data.

    Lets a single test case be reused across many data rows: an XPath or Data
    cell written as ``{{username}}`` becomes that row's username. Non-string
    cells (e.g. blank cells, which pandas reads as NaN) pass through untouched.
    """
    if not isinstance(value, str):
        return value
    for key, val in data_row.items():
        placeholder = f"{{{{{key}}}}}"
        value = value.replace(placeholder, str(val))
    return value


# Matches a {{placeholder}} token, tolerating inner whitespace: {{ user }}.
PLACEHOLDER_RE = re.compile(r"\{\{\s*\w+\s*\}\}")


def has_placeholders(df) -> bool:
    """True if any cell in the workbook contains a ``{{placeholder}}`` token.

    Data-driven replay only makes sense when there is something to substitute.
    Without this check a workbook is replayed once per row of the data file
    purely because that file happens to exist -- running an identical test N
    times and reporting N copies of the same result.

    Args:
        df: The test workbook as a DataFrame.
    """
    # str() per cell rather than df.astype(str): with mixed dtypes astype can
    # leave NaN as a float, which the regex then chokes on.
    return any(
        PLACEHOLDER_RE.search(str(cell))
        for cell in df.to_numpy().ravel()
    )


# =========================================================
# Helper: Load data file (if uploaded)
# =========================================================
def load_data_file(file):
    """Read an Excel file into a list of row dicts.

    Returns an empty list if the file is missing or unreadable, because a
    data file is optional -- a test without one simply runs a single pass.
    """
    try:
        df = pd.read_excel(file)
        return df.to_dict(orient="records")
    except Exception:
        return []


# =========================================================
# Main Test Runner
# =========================================================
def run_test_from_excel(file):
    """Execute every step in an Excel test workbook and build the reports.

    Args:
        file: An uploaded file object (Streamlit) or path readable by pandas.
            Must expose ``.name``, which is used to name the output files.

    Returns:
        ``(all_test_runs, html_path, pdf_path)``. For a *data* workbook
        (empty Action column) returns ``(rows, None, None)`` instead, since
        there is nothing to execute and no report to generate.

    Raises:
        Exception: If a required column is missing from the workbook.
    """
    df = pd.read_excel(file)
    filename = os.path.splitext(file.name)[0]

    # Validate required columns
    required_cols = ["Description", "XPath", "Action", "Data"]
    for col in required_cols:
        if col not in df.columns:
            raise Exception(f"Missing required column: {col}")

    # Detect if this is a data file
    is_data_file = df["Action"].isna().all()
    if is_data_file:
        return load_data_file(file), None, None

    # Only start a browser if the workbook actually drives one. An API-only
    # workbook (all api_* actions) runs over plain HTTP, so launching Chrome
    # would be wasted startup time -- and would fail outright on a machine
    # with no Chrome installed.
    if requires_browser(df["Action"]):
        # Honours HEADLESS / WINDOW_SIZE / DEFAULT_TIMEOUT from settings.
        driver = create_driver()
    else:
        driver = None
        print("No UI steps detected - running API-only, skipping browser launch")

    # Optional data-driven replay: run the test body once per row of test data.
    # Only worth doing when the workbook actually contains {{placeholders}} --
    # otherwise every replay produces an identical result, so we'd just be
    # running the same test N times and reporting N copies of the same thing.
    data_rows = []
    if has_placeholders(df):
        # Missing/unreadable data file is fine: load_data_file returns [] and
        # we fall back to a single pass below.
        data_rows = load_data_file(TEST_DATA_DIR / "generated_data.xlsx")
        if not data_rows:
            print("Test uses {{placeholders}} but no test data found - running once")
    if not data_rows:
        data_rows = [{}]  # single pass, nothing to substitute

    all_test_runs = []

    try:
        # Run test once per data row
        for test_index, data_row in enumerate(data_rows):
            test_result = {
                "test_id": test_index + 1,
                "steps": []
            }

            for idx, row in df.iterrows():
                desc = row["Description"]
                xpath = substitute_placeholders(row["XPath"], data_row)
                action = str(row["Action"]).strip()
                data = substitute_placeholders(row["Data"], data_row)

                status = "PASS"
                error = ""
                ai_help = ""

                try:
                    if action not in KEYWORD_MAP:
                        raise Exception(f"Unknown action: {action}")

                    KEYWORD_MAP[action](
                        driver,
                        xpath if xpath != "N/A" else None,
                        data
                    )
                    time.sleep(0.3)

                except Exception as e:
                    status = "FAIL"
                    error = str(e)
                    ai_help = ai_explain_failure(
                        {
                            "Description": desc,
                            "XPath": xpath,
                            "Action": action,
                            "Data": data or "",
                        },
                        error,
                    )

                test_result["steps"].append({
                    "Step": idx + 1,
                    "Description": desc,
                    "Action": action,
                    "Status": status,
                    "Error": error,
                    "AI Help": ai_help
                })

            all_test_runs.append(test_result)

    finally:
        # driver is None for API-only runs; nothing to close.
        if driver is not None:
            try:
                driver.quit()
            except WebDriverException:
                pass

    # =========================================================
    # Generate Summary Chart
    # =========================================================
    total_pass = sum(
        1 for test in all_test_runs for step in test["steps"] if step["Status"] == "PASS"
    )
    total_fail = sum(
        1 for test in all_test_runs for step in test["steps"] if step["Status"] == "FAIL"
    )

    # Pie chart of overall pass/fail, embedded into the HTML report below.
    chart_path = str(REPORTS_DIR / f"{filename}_chart.png")

    plt.figure(figsize=(4, 4))
    plt.pie(
        [total_pass, total_fail],
        labels=["PASS", "FAIL"],
        autopct='%1.1f%%',
        colors=["#4CAF50", "#F44336"]
    )
    plt.title("Overall Execution Status")
    plt.savefig(chart_path)
    plt.close()

    # =========================================================
    # Generate Reports ONCE (AFTER all test runs)
    # =========================================================
    html_path = generate_html_report(all_test_runs, filename, chart_path)
    pdf_path = generate_pdf_report(all_test_runs, filename)

    return all_test_runs, html_path, pdf_path


# =========================================================
# HTML Report Generator
# =========================================================
def generate_html_report(all_tests, filename, chart_path):
    """Render the run summary as a standalone HTML dashboard.

    Written to ``outputs/reports/<filename>_report.html``. The pie chart is
    referenced by basename so the .html and .png stay portable as a pair --
    move both together and the image still resolves.

    Returns:
        str: Full path to the written file.
    """
    path = str(REPORTS_DIR / f"{filename}_report.html")
    chart_src = os.path.basename(chart_path)

    html = f"""
    <html><head><title>Automation Report</title></head>
    <body>
    <h1>Automation Execution Report</h1>
    <h2>Overall Results</h2>
    <img src="{chart_src}" width="300">
    <hr>
    """

    for test in all_tests:
        html += f"<h2>Test Run {test['test_id']}</h2>"
        html += """
        <table border="1" cellpadding="5">
        <tr>
            <th>Step</th><th>Description</th><th>Action</th><th>Status</th><th>Error</th><th>AI Help</th>
        </tr>
        """
        for r in test["steps"]:
            html += (
                f"<tr><td>{r['Step']}</td>"
                f"<td>{r['Description']}</td>"
                f"<td>{r['Action']}</td>"
                f"<td>{r['Status']}</td>"
                f"<td>{r['Error']}</td>"
                f"<td>{r['AI Help']}</td></tr>"
            )
        html += "</table><br>"

    html += "</body></html>"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return path


# =========================================================
# PDF Report Generator
# =========================================================
def generate_pdf_report(all_tests, filename):
    """Render the same run summary as a printable PDF.

    Written to ``outputs/reports/<filename>_report.pdf``. Deliberately plain
    text -- FPDF's core fonts are latin-1 only, so no emoji or box-drawing
    characters here.

    Returns:
        str: Full path to the written file.
    """
    path = str(REPORTS_DIR / f"{filename}_report.pdf")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="Automation Execution Report", ln=True)

    for test in all_tests:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 5, txt=f"Test Run {test['test_id']}", ln=True)

        pdf.set_font("Arial", size=9)
        for r in test["steps"]:
            line = f"{r['Step']}. {r['Description']} - {r['Status']}"
            pdf.multi_cell(0, 5, txt=line)

    pdf.output(path)
    return path
