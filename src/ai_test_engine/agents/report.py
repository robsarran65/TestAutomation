"""
The Report agent: turns raw test results into shareable artifacts.

Consumes the result dict produced by the Test Executor and renders it as:
    generate_html_report - a styled standalone HTML dashboard
    generate_pdf_report  - a printable PDF summary
    generate_summary     - a quick text/metrics summary for the console or UI

Everything is written to ``outputs/reports/`` by default (see settings.py).
Files are written as UTF-8 because the templates contain check/cross glyphs
that would fail under Windows' default cp1252 codec.
"""

# =========================================================
# REPORT AGENT - Aggregates results and generates reports
# =========================================================

from typing import Any, Dict, List
from datetime import datetime
import json
import traceback
import os

from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO

from ai_test_engine.agents.agent_base import Agent, AgentType, TaskMessage, TaskResult, TaskStatus
from ai_test_engine.config.settings import REPORTS_DIR


def normalize_test_results(test_results: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce either executor result shape into the one the renderers read.

    The Test Executor returns two different shapes. A single run
    (``run_test_cases``) uses::

        total_steps / passed_steps / failed_steps / success_rate / steps

    while a data-driven run (``run_data_driven_test``) uses::

        total_steps_executed / total_passed / total_failed /
        overall_success_rate / iterations[].steps

    Every renderer below reads the first set only, so a data-driven result
    passed straight through rendered a report claiming 0 steps and 0 passed
    for a run that really executed dozens. Normalising here rather than at each
    call site means any caller -- the demo workflow, scripts, the UI -- gets a
    correct report without knowing which action produced the results.

    Single-run results and unrecognised shapes are returned unchanged.
    """
    if test_results.get("test_type") != "data_driven":
        return test_results

    steps: List[Dict[str, Any]] = []
    for iteration in test_results.get("iterations", []):
        row_num = iteration.get("data_row_num")
        for step in iteration.get("steps", []):
            # Prefix the row number so a 5-step workbook run over 3 rows reads
            # as 15 distinct rows rather than three identical-looking blocks.
            steps.append({**step, "description": f"[row {row_num}] {step.get('description', '')}"})

    return {
        **test_results,
        "total_steps": test_results.get("total_steps_executed", 0),
        "passed_steps": test_results.get("total_passed", 0),
        "failed_steps": test_results.get("total_failed", 0),
        "success_rate": test_results.get("overall_success_rate", 0),
        "steps": steps,
        # Iterations each carry their own duration; the renderers want one
        # number for the whole run.
        "duration_sec": sum(
            it.get("duration_sec", 0) for it in test_results.get("iterations", [])
        ),
    }


class ReportAgent(Agent):
    """
    Generates comprehensive test reports in multiple formats.
    
    Actions:
    - generate_html_report: Create interactive HTML report
    - generate_pdf_report: Create PDF with charts
    - generate_summary: Quick text summary
    """
    
    def __init__(self, output_dir: str = None):
        """Create the agent.

        Args:
            output_dir: Where reports are written. Defaults to the project's
                ``outputs/reports/``. Anchored to the repo, never the current
                working directory, so output lands in the same place no matter
                where the process was launched from.
        """
        super().__init__(AgentType.REPORT, "Report Generator")
        self.output_dir = str(output_dir or REPORTS_DIR)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def execute(self, task: TaskMessage) -> TaskResult:
        """Execute report generation task"""
        
        result = TaskResult(
            task_id=task.task_id,
            agent_type=self.agent_type,
            status=TaskStatus.COMPLETED,
        )
        
        try:
            if task.action == "generate_html_report":
                result.result = self.generate_html_report(
                    task.payload.get("test_results", {}),
                    task.payload.get("filename", "test_report"),
                    task.payload.get("title", "Test Execution Report")
                )
                
            elif task.action == "generate_pdf_report":
                result.result = self.generate_pdf_report(
                    task.payload.get("test_results", {}),
                    task.payload.get("filename", "test_report")
                )
                
            elif task.action == "generate_summary":
                result.result = self.generate_summary(
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
    
    def generate_html_report(
        self,
        test_results: Dict[str, Any],
        filename: str = "test_report",
        title: str = "Test Execution Report"
    ) -> Dict[str, Any]:
        """
        Generate interactive HTML report.
        
        Returns:
            {"filepath": "...", "url": "...", "summary": {...}}
        """
        print(f"📊 Generating HTML report: {filename}")

        test_results = normalize_test_results(test_results)

        # Extract test metrics
        total_steps = test_results.get("total_steps", 0)
        passed = test_results.get("passed_steps", 0)
        failed = test_results.get("failed_steps", 0)
        success_rate = test_results.get("success_rate", 0)
        
        # Build HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary {{
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                .metric {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .metric-label {{
                    color: #7f8c8d;
                    font-size: 12px;
                    margin-top: 5px;
                }}
                .pass {{ color: #27ae60; }}
                .fail {{ color: #e74c3c; }}
                .steps {{
                    background-color: white;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .step {{
                    padding: 10px;
                    border-left: 4px solid #bdc3c7;
                    margin: 10px 0;
                }}
                .step.pass {{
                    border-left-color: #27ae60;
                    background-color: #ecf0f1;
                }}
                .step.fail {{
                    border-left-color: #e74c3c;
                    background-color: #fadbd8;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                th, td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #34495e;
                    color: white;
                }}
                tr:hover {{
                    background-color: #f9f9f9;
                }}
                .progress-bar {{
                    width: 100%;
                    height: 20px;
                    background-color: #ecf0f1;
                    border-radius: 10px;
                    overflow: hidden;
                    margin-top: 5px;
                }}
                .progress-fill {{
                    height: 100%;
                    background-color: #27ae60;
                    width: {success_rate}%;
                    transition: width 0.3s ease;
                }}
                .timestamp {{
                    color: #7f8c8d;
                    font-size: 12px;
                    margin-top: 20px;
                    text-align: right;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 {title}</h1>
                <p>Automated Test Execution Report</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <div class="metric-value">{total_steps}</div>
                    <div class="metric-label">Total Steps</div>
                </div>
                <div class="metric">
                    <div class="metric-value pass">{passed}</div>
                    <div class="metric-label">Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value fail">{failed}</div>
                    <div class="metric-label">Failed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{success_rate:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
            
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
            
            <div class="steps">
                <h2>Test Steps Detail</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Description</th>
                            <th>Action</th>
                            <th>Status</th>
                            <th>Duration (ms)</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add step rows
        for step in test_results.get("steps", []):
            status_class = "pass" if step["status"] == "PASS" else "fail"
            html_content += f"""
                        <tr>
                            <td>{step['step_num']}</td>
                            <td>{step['description']}</td>
                            <td>{step['action']}</td>
                            <td><span class="{status_class}">{step['status']}</span></td>
                            <td>{step['duration_ms']}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <div class="timestamp">
                Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
            </div>
        </body>
        </html>
        """
        
        # Save to file
        filepath = os.path.join(self.output_dir, f"{filename}_report.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ HTML report saved: {filepath}")
        
        return {
            "filepath": filepath,
            "format": "html",
            "test_count": len(test_results.get("steps", [])),
            "summary": {
                "passed": passed,
                "failed": failed,
                "total": total_steps,
                "success_rate": success_rate,
            }
        }
    
    def generate_pdf_report(
        self,
        test_results: Dict[str, Any],
        filename: str = "test_report"
    ) -> Dict[str, Any]:
        """
        Generate PDF report with charts.
        
        Returns:
            {"filepath": "...", "summary": {...}}
        """
        print(f"📄 Generating PDF report: {filename}")

        test_results = normalize_test_results(test_results)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Test Execution Report", ln=True)
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        
        # Summary metrics
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Summary", ln=True)
        
        pdf.set_font("Arial", "", 11)
        total = test_results.get("total_steps", 0)
        passed = test_results.get("passed_steps", 0)
        failed = test_results.get("failed_steps", 0)
        
        pdf.cell(0, 8, f"Total Steps: {total}", ln=True)
        pdf.cell(0, 8, f"Passed: {passed}", ln=True)
        pdf.cell(0, 8, f"Failed: {failed}", ln=True)
        pdf.cell(0, 8, f"Success Rate: {test_results.get('success_rate', 0):.1f}%", ln=True)
        
        # Save PDF
        filepath = os.path.join(self.output_dir, f"{filename}_report.pdf")
        pdf.output(filepath)
        
        print(f"✅ PDF report saved: {filepath}")
        
        return {
            "filepath": filepath,
            "format": "pdf",
            "pages": 1,
        }
    
    def generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quick text summary.
        
        Returns:
            Summary dict with key metrics
        """
        test_results = normalize_test_results(test_results)

        total = test_results.get("total_steps", 0)
        passed = test_results.get("passed_steps", 0)
        failed = test_results.get("failed_steps", 0)
        rate = test_results.get("success_rate", 0)
        
        summary_text = f"""
        ╔════════════════════════════════════════╗
        ║     TEST EXECUTION SUMMARY             ║
        ╚════════════════════════════════════════╝
        
        Total Steps:    {total}
        ✅ Passed:      {passed}
        ❌ Failed:      {failed}
        Success Rate:   {rate:.1f}%
        
        Duration:       {test_results.get('duration_sec', 0):.2f}s
        Environment:    {test_results.get('environment', 'N/A')}
        
        Timestamp:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        print(summary_text)
        
        return {
            "summary_text": summary_text,
            "metrics": {
                "total_steps": total,
                "passed": passed,
                "failed": failed,
                "success_rate": rate,
            }
        }
