"""
Streamlit UI (classic single-agent mode).

Upload an Excel test workbook, pick an environment, run it, and download the
resulting HTML/PDF reports. Execution goes straight to
``core.test_runner.run_test_from_excel`` with no Coordinator involved.

Run with:  streamlit run src/ai_test_engine/app.py

See app_multiagent.py for the multi-agent version.
"""

import streamlit as st
import pandas as pd
from io import BytesIO

# Import framework modules
from ai_test_engine.core.test_runner import run_test_from_excel
from ai_test_engine.core.ai_engine import (
    ai_generate_test_from_description,
    ai_optimize_test_suite,
    ai_generate_test_data
)

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI‑Powered Test Automation Framework",
    layout="wide"
)

st.title("🤖 AI‑Powered Scriptless Test Automation Framework")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "Run Test Cases",
        "AI: Generate Test From Description",
        "AI: Generate Test Data",
        "AI: Optimize Test Suite"
    ]
)

# ---------------------------------------------------------
# SIDEBAR ENVIRONMENT SELECTOR
# ---------------------------------------------------------
st.sidebar.header("Environment")
env = st.sidebar.selectbox("Select environment", ["DEV", "TEST", "PROD"])
st.sidebar.write(f"Current environment: **{env}**")


# =========================================================
# PAGE 1 — RUN TEST CASES
# =========================================================
if page == "Run Test Cases":
    st.header("📄 Upload & Run Test Cases")

    uploaded_files = st.file_uploader(
        "Upload one or more Excel test files",
        type=["xlsx"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("Run All Tests"):
            for file in uploaded_files:
                st.subheader(f"Running: {file.name}")

                results, html_path, pdf_path = run_test_from_excel(file)

                st.dataframe(results)

                # Download HTML report
                with open(html_path, "rb") as f:
                    st.download_button(
                        f"Download HTML Report for {file.name}",
                        data=f,
                        file_name=f"{file.name}.html",
                        mime="text/html"
                    )

                # Download PDF report
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        f"Download PDF Report for {file.name}",
                        data=f,
                        file_name=f"{file.name}.pdf",
                        mime="application/pdf"
                    )


# =========================================================
# PAGE 2 — AI: GENERATE TEST FROM DESCRIPTION
# =========================================================
elif page == "AI: Generate Test From Description":
    st.header("🧠 AI: Generate Test From Description")

    description = st.text_area(
        "Describe the test you want (e.g., 'Login with valid credentials')"
    )

    if st.button("Generate Test Steps"):
        if description.strip():
            steps = ai_generate_test_from_description(description)
            df = pd.DataFrame(steps)

            st.subheader("Generated Test Steps")
            st.dataframe(df)

            # Convert to Excel for download
            buffer = BytesIO()
            df.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                "Download as Excel",
                data=buffer,
                file_name="generated_test.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Please enter a description.")


# =========================================================
# PAGE 3 — AI: GENERATE TEST DATA
# =========================================================
elif page == "AI: Generate Test Data":
    st.header("🧠 AI: Generate Test Data")

    schema = st.text_input(
        "Describe the data you need (e.g., 'usernames and passwords')"
    )

    if st.button("Generate Data"):
        if schema.strip():
            data = ai_generate_test_data(schema)
            df_data = pd.DataFrame(data)

            st.subheader("Generated Data")
            st.dataframe(df_data)

            # Convert to Excel
            buffer = BytesIO()
            df_data.to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)

            st.download_button(
                "Download Data as Excel",
                data=buffer,
                file_name="generated_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Please describe the data you need.")


# =========================================================
# PAGE 4 — AI: OPTIMIZE TEST SUITE
# =========================================================
elif page == "AI: Optimize Test Suite":
    st.header("🧠 AI: Optimize Test Suite")

    st.write("Upload test files to analyze redundancy and optimization opportunities.")

    suite_files = st.file_uploader(
        "Upload test suite files",
        type=["xlsx"],
        accept_multiple_files=True
    )

    if suite_files and st.button("Analyze & Suggest Optimizations"):
        summaries = [{"name": f.name, "type": "Unknown"} for f in suite_files]

        suggestion = ai_optimize_test_suite(summaries)

        st.subheader("AI Optimization Suggestions")
        st.text_area("AI Output", suggestion, height=200)
