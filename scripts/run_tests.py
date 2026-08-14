# =========================================================
# DEMO: Web Form + API Test Execution with Multi-Agent
# =========================================================
"""
This script demonstrates:
1. Web Form Test (Login)
2. API Test (Weather API)
Both tests run through the Coordinator Agent
Results displayed in HTML format
"""

from datetime import datetime
import json
from io import StringIO

from ai_test_engine.config.settings import REPORTS_DIR

# =========================================================
# MOCK COORDINATOR (for demo purposes)
# =========================================================

class MockCoordinator:
    """Simulates coordinator for demo without real dependencies"""
    
    def __init__(self):
        """Create the mock. Holds results keyed by test name."""
        self.results = {}
    
    def execute_web_form_test(self):
        """Simulate web form test execution"""
        test_steps = [
            {
                "step_num": 1,
                "description": "Navigate to login page",
                "action": "launch_url",
                "status": "PASS",
                "duration_ms": 1200,
                "error": ""
            },
            {
                "step_num": 2,
                "description": "Enter username 'admin'",
                "action": "enter_text",
                "status": "PASS",
                "duration_ms": 340,
                "error": ""
            },
            {
                "step_num": 3,
                "description": "Enter password 'password123'",
                "action": "enter_text",
                "status": "PASS",
                "duration_ms": 280,
                "error": ""
            },
            {
                "step_num": 4,
                "description": "Click login button",
                "action": "click",
                "status": "PASS",
                "duration_ms": 450,
                "error": ""
            },
            {
                "step_num": 5,
                "description": "Verify dashboard loaded",
                "action": "verify_text",
                "status": "PASS",
                "duration_ms": 580,
                "error": ""
            }
        ]
        
        return {
            "test_name": "Web Form - Login Test",
            "test_type": "UI",
            "total_steps": len(test_steps),
            "passed_steps": 5,
            "failed_steps": 0,
            "success_rate": 100.0,
            "steps": test_steps,
            "environment": "TEST",
            "duration_sec": 3.85,
            "url": "https://example.com/login",
            "browser": "Chrome"
        }
    
    def execute_api_test(self):
        """Simulate API test execution"""
        test_steps = [
            {
                "step_num": 1,
                "description": "Send GET request to weather API",
                "action": "api_get",
                "status": "PASS",
                "duration_ms": 245,
                "error": ""
            },
            {
                "step_num": 2,
                "description": "Verify HTTP 200 status code",
                "action": "api_verify_status",
                "status": "PASS",
                "duration_ms": 120,
                "error": ""
            },
            {
                "step_num": 3,
                "description": "Verify temperature field exists",
                "action": "api_verify_json_field",
                "status": "PASS",
                "duration_ms": 85,
                "error": ""
            },
            {
                "step_num": 4,
                "description": "Verify location matches request",
                "action": "api_verify_json_field",
                "status": "PASS",
                "duration_ms": 92,
                "error": ""
            },
            {
                "step_num": 5,
                "description": "Extract and save temperature",
                "action": "api_save_field",
                "status": "PASS",
                "duration_ms": 110,
                "error": ""
            }
        ]
        
        return {
            "test_name": "API Test - Weather Service",
            "test_type": "API",
            "total_steps": len(test_steps),
            "passed_steps": 5,
            "failed_steps": 0,
            "success_rate": 100.0,
            "steps": test_steps,
            "environment": "TEST",
            "duration_sec": 0.652,
            "endpoint": "https://api.weather.example.com/forecast",
            "method": "GET"
        }


# =========================================================
# HTML REPORT GENERATOR
# =========================================================

class ReportGenerator:
    """Generate HTML reports from test results"""
    
    @staticmethod
    def generate_html_report(test_results, filename="test_report.html"):
        """Generate a complete HTML report with styling"""
        
        total_steps = test_results.get("total_steps", 0)
        passed = test_results.get("passed_steps", 0)
        failed = test_results.get("failed_steps", 0)
        success_rate = test_results.get("success_rate", 0)
        test_name = test_results.get("test_name", "Test Report")
        test_type = test_results.get("test_type", "Unknown")
        duration = test_results.get("duration_sec", 0)
        
        # Determine badge color
        if success_rate == 100:
            badge_color = "#27ae60"  # Green
            badge_text = "✓ PASSED"
        elif success_rate >= 50:
            badge_color = "#f39c12"  # Orange
            badge_text = "⚠ PARTIAL"
        else:
            badge_color = "#e74c3c"  # Red
            badge_text = "✗ FAILED"
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{test_name} - Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 40px;
            text-align: center;
            border-bottom: 4px solid {badge_color};
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .badge {{
            display: inline-block;
            background: {badge_color};
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 15px;
            font-size: 0.95em;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .metric {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid {badge_color};
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .progress-container {{
            margin-bottom: 30px;
        }}
        
        .progress-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 24px;
            background: #ecf0f1;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {badge_color} 0%, {badge_color}dd 100%);
            width: {success_rate}%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
            transition: width 0.3s ease;
        }}
        
        .section-title {{
            font-size: 1.5em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        
        .steps-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        
        .steps-table th {{
            background: #34495e;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}
        
        .steps-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        .steps-table tbody tr {{
            transition: background 0.2s ease;
        }}
        
        .steps-table tbody tr:hover {{
            background: #f9f9f9;
        }}
        
        .step-num {{
            font-weight: bold;
            color: #667eea;
            width: 40px;
        }}
        
        .status-pass {{
            color: #27ae60;
            font-weight: bold;
            display: inline-block;
            padding: 4px 8px;
            background: #d5f4e6;
            border-radius: 4px;
        }}
        
        .status-fail {{
            color: #e74c3c;
            font-weight: bold;
            display: inline-block;
            padding: 4px 8px;
            background: #fadbd8;
            border-radius: 4px;
        }}
        
        .duration {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .test-info {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            font-size: 0.9em;
        }}
        
        .test-info-item {{
            padding: 10px;
        }}
        
        .test-info-label {{
            color: #7f8c8d;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 0.5px;
        }}
        
        .test-info-value {{
            color: #2c3e50;
            font-weight: 500;
            margin-top: 4px;
            word-break: break-all;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #ecf0f1;
        }}
        
        .timestamp {{
            color: #95a5a6;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Test Execution Report</h1>
            <p>{test_name}</p>
            <div class="badge">{badge_text}</div>
        </div>
        
        <div class="content">
            <!-- Test Info -->
            <div class="test-info">
                <div class="test-info-item">
                    <div class="test-info-label">Test Type</div>
                    <div class="test-info-value">{test_type}</div>
                </div>
                <div class="test-info-item">
                    <div class="test-info-label">Environment</div>
                    <div class="test-info-value">{test_results.get('environment', 'N/A')}</div>
                </div>
                <div class="test-info-item">
                    <div class="test-info-label">Duration</div>
                    <div class="test-info-value">{duration:.3f}s</div>
                </div>
                <div class="test-info-item">
                    <div class="test-info-label">Executed</div>
                    <div class="test-info-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
            </div>
            
            <!-- Summary Metrics -->
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{total_steps}</div>
                    <div class="metric-label">Total Steps</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #27ae60;">✓ {passed}</div>
                    <div class="metric-label">Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #e74c3c;">✗ {failed}</div>
                    <div class="metric-label">Failed</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: {badge_color};">{success_rate:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
            </div>
            
            <!-- Progress Bar -->
            <div class="progress-container">
                <div class="progress-label">
                    <span>Test Progress</span>
                    <span>{success_rate:.1f}% Complete</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {success_rate}%">
                        {success_rate:.0f}%
                    </div>
                </div>
            </div>
            
            <!-- Test Steps -->
            <h2 class="section-title">📋 Test Execution Details</h2>
            <table class="steps-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Description</th>
                        <th>Action</th>
                        <th>Status</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Add step rows
        for step in test_results.get("steps", []):
            status_class = "status-pass" if step["status"] == "PASS" else "status-fail"
            status_icon = "✓" if step["status"] == "PASS" else "✗"
            
            html += f"""
                    <tr>
                        <td class="step-num">{step['step_num']}</td>
                        <td>{step['description']}</td>
                        <td><code>{step['action']}</code></td>
                        <td><span class="{status_class}">{status_icon} {step['status']}</span></td>
                        <td class="duration">{step['duration_ms']}ms</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>Generated by 🤖 Multi-Agent Test Automation Framework</p>
            <p class="timestamp">Report generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html


# =========================================================
# MAIN EXECUTION
# =========================================================

def main():
    """Run both demo tests and write their HTML reports to outputs/reports/."""
    print("=" * 70)
    print("  🤖 MULTI-AGENT TEST AUTOMATION - WEB FORM & API TESTS")
    print("=" * 70)
    print()
    
    # Initialize coordinator
    coordinator = MockCoordinator()
    
    # =========================================================
    # TEST 1: WEB FORM TEST
    # =========================================================
    print("📋 TEST 1: Web Form Login Test")
    print("-" * 70)
    
    web_form_results = coordinator.execute_web_form_test()
    
    print(f"  Test: {web_form_results['test_name']}")
    print(f"  Type: {web_form_results['test_type']}")
    print(f"  URL: {web_form_results['url']}")
    print(f"  Browser: {web_form_results['browser']}")
    print(f"  Steps: {web_form_results['passed_steps']}/{web_form_results['total_steps']} passed")
    print(f"  Duration: {web_form_results['duration_sec']:.3f}s")
    print(f"  Result: {'✅ PASSED' if web_form_results['success_rate'] == 100 else '❌ FAILED'}")
    print()
    
    # Generate HTML report for web form test
    report_gen = ReportGenerator()
    web_form_html = report_gen.generate_html_report(web_form_results, "web_form_test_report.html")
    
    with open(REPORTS_DIR / "web_form_test_report.html", "w", encoding="utf-8") as f:
        f.write(web_form_html)
    
    print("  ✓ HTML report saved to: outputs/reports/web_form_test_report.html")
    print()
    
    # =========================================================
    # TEST 2: API TEST
    # =========================================================
    print("📋 TEST 2: API Weather Service Test")
    print("-" * 70)
    
    api_results = coordinator.execute_api_test()
    
    print(f"  Test: {api_results['test_name']}")
    print(f"  Type: {api_results['test_type']}")
    print(f"  Endpoint: {api_results['endpoint']}")
    print(f"  Method: {api_results['method']}")
    print(f"  Steps: {api_results['passed_steps']}/{api_results['total_steps']} passed")
    print(f"  Duration: {api_results['duration_sec']:.3f}s")
    print(f"  Result: {'✅ PASSED' if api_results['success_rate'] == 100 else '❌ FAILED'}")
    print()
    
    # Generate HTML report for API test
    api_html = report_gen.generate_html_report(api_results, "api_test_report.html")
    
    with open(REPORTS_DIR / "api_test_report.html", "w", encoding="utf-8") as f:
        f.write(api_html)
    
    print("  ✓ HTML report saved to: outputs/reports/api_test_report.html")
    print()
    
    # =========================================================
    # COMBINED SUMMARY
    # =========================================================
    print("=" * 70)
    print("  📊 TEST EXECUTION SUMMARY")
    print("=" * 70)
    print()
    
    total_steps = web_form_results['total_steps'] + api_results['total_steps']
    total_passed = web_form_results['passed_steps'] + api_results['passed_steps']
    total_failed = web_form_results['failed_steps'] + api_results['failed_steps']
    overall_rate = (total_passed / total_steps * 100) if total_steps > 0 else 0
    
    print(f"  Total Tests Run: 2")
    print(f"  Total Steps: {total_steps}")
    print(f"  ✅ Passed: {total_passed}")
    print(f"  ❌ Failed: {total_failed}")
    print(f"  📊 Success Rate: {overall_rate:.1f}%")
    print()
    
    print("  Test Results:")
    print(f"    1. Web Form Test: {'✅ PASSED' if web_form_results['success_rate'] == 100 else '❌ FAILED'}")
    print(f"    2. API Test: {'✅ PASSED' if api_results['success_rate'] == 100 else '❌ FAILED'}")
    print()
    
    print("  📄 Generated Reports:")
    print("    • outputs/reports/web_form_test_report.html")
    print("    • outputs/reports/api_test_report.html")
    print()
    
    print("=" * 70)
    print("  ✅ TEST EXECUTION COMPLETE")
    print("=" * 70)
    
    # Return the HTML reports for display
    return {
        "web_form_html": web_form_html,
        "api_html": api_html,
        "web_form_results": web_form_results,
        "api_results": api_results
    }


if __name__ == "__main__":
    results = main()
