import json
import sys
import os

# Add backend dir to path
sys.path.append(os.path.abspath("e:/Adarsh/Hackathon Projects/Design-Guide/designguard/backend"))

from report_generator import generate_pdf_report

mock_scan = {
    "url": "https://example.com",
    "scan_id": "test_scan_123",
    "quality_score": 85,
    "all_bugs": [
        {"severity": "critical", "bug_id": "BUG_001", "category": "layout", "label": "Broken Button", "description": "The login button is overlapping with text.", "element": "button.login", "css_fix": "margin-top: 10px;", "devtools_command": "document.querySelector('button.login').style.marginTop = '10px'"},
        {"severity": "serious", "bug_id": "BUG_002", "category": "color", "label": "Low Contrast", "description": "Text is hard to read against the gray background.", "element": "p.text", "css_fix": "color: #000;", "devtools_command": "document.querySelector('p.text').style.color = '#000'"}
    ],
    "network_issues": [
        {"type": "api_error", "severity": "serious", "url": "https://api.example.com/v1/user", "description": "401 Unauthorized", "fix": "Check auth token renewal."}
    ],
    "performance_metrics": {
        "initial_load_ms": 1200,
        "pages_scanned": 1,
        "total_requests": 25,
        "error_count": 1,
        "slow_request_count": 0
    },
    "pages_visited": ["https://example.com"],
    "created_at": "2024-03-16T12:00:00Z"
}

try:
    pdf_bytes = generate_pdf_report(mock_scan)
    with open("test_report.pdf", "wb") as f:
        f.write(pdf_bytes)
    print("SUCCESS: PDF generated as test_report.pdf")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
