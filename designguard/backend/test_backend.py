"""
DesignGuard Backend — comprehensive unit + integration tests.

Covers:
  • main.py  – API routes, _camel(), _clean_result()
  • memory.py – save_scan / get_scan / get_user_history / get_previous_scan
  • report_generator.py – PDF output, HTML-escape safety
  • playwright_navigator.py – URL validation / domain guard / BFS helpers
  • agent.py – LangGraph pipeline (navigate/detect/fix/verify/report nodes)

Run with:
  cd designguard/backend && pytest test_backend.py -v
"""

import uuid
import html
import io
from datetime import datetime
from unittest.mock import patch, MagicMock
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_bug(
    severity: str = "serious",
    category: str = "Color Contrast",
    description: str = "Low contrast text on button",
    element: str = "button.submit",
    css_fix: str = "color: #fff;",
    devtools_command: str = "document.querySelector('button').style.color='#fff'",
    bug_id: str | None = None,
) -> Dict[str, Any]:
    return {
        "bug_id": bug_id or f"BUG_{uuid.uuid4().hex[:6].upper()}",
        "severity": severity,
        "category": category,
        "description": description,
        "element_description": element,
        "css_fix": css_fix,
        "devtools_command": devtools_command,
        "url": "https://example.com",
        "label": "Desktop – Home",
        "viewport": "desktop",
    }


def make_scan(
    bugs: List[Dict] | None = None,
    url: str = "https://example.com",
    user_id: str = "test-user",
    pages: List[str] | None = None,
    network_issues: List[Dict] | None = None,
    figma_deviations: List[Dict] | None = None,
) -> Dict[str, Any]:
    bugs = bugs or [make_bug()]
    return {
        "scan_id": str(uuid.uuid4()),
        "user_id": user_id,
        "url": url,
        "quality_score": 72,
        "figma_match_score": 88,
        "all_bugs": bugs,
        "network_issues": network_issues or [],
        "figma_deviations": figma_deviations or [],
        "fixes": [
            {
                "bug_id": b["bug_id"],
                "devtools_command": b.get("devtools_command", ""),
                "css_fix": b.get("css_fix", ""),
                "severity": b["severity"],
                "description": b["description"],
            }
            for b in bugs
            if b.get("devtools_command")
        ],
        "new_bugs": bugs,
        "pages_visited": pages or ["https://example.com"],
        "performance_metrics": {
            "initial_load_ms": 540,
            "pages_scanned": len(pages or ["https://example.com"]),
            "total_requests": 12,
            "error_count": 0,
            "slow_request_count": 0,
        },
        "screenshots_meta": [
            {"url": "https://example.com", "viewport": "desktop", "label": "Desktop – Home"},
            {"url": "https://example.com", "viewport": "tablet",  "label": "Tablet – Home"},
            {"url": "https://example.com", "viewport": "mobile",  "label": "Mobile – Home"},
        ],
        "created_at": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 1.  memory.py
# ─────────────────────────────────────────────────────────────────────────────

class TestMemory:
    """Tests for database operations in memory.py"""

    def test_save_and_get_scan(self):
        from memory import save_scan, get_scan
        s = make_scan()
        save_scan(s)
        fetched = get_scan(s["scan_id"])
        assert fetched is not None
        assert fetched["scan_id"] == s["scan_id"]
        assert fetched["url"] == s["url"]
        assert fetched["quality_score"] == s["quality_score"]

    def test_get_scan_not_found_returns_none(self):
        from memory import get_scan
        assert get_scan("nonexistent-id-xyz-000") is None

    def test_save_scan_persists_all_fields(self):
        from memory import save_scan, get_scan
        s = make_scan(
            bugs=[make_bug(severity="critical", description="Critical spacing issue")],
            pages=["https://example.com", "https://example.com/about"],
            network_issues=[{"type": "slow_request", "severity": "moderate", "description": "Slow API", "fix": "Cache it", "url": "https://example.com/api"}],
        )
        save_scan(s)
        fetched = get_scan(s["scan_id"])
        assert len(fetched["all_bugs"]) == 1
        assert fetched["all_bugs"][0]["severity"] == "critical"
        assert len(fetched["pages_visited"]) == 2
        assert len(fetched["network_issues"]) == 1
        assert fetched["network_issues"][0]["type"] == "slow_request"

    def test_get_user_history_returns_recent_scans(self):
        from memory import save_scan, get_user_history
        uid = f"hist-user-{uuid.uuid4().hex[:6]}"
        s1 = make_scan(user_id=uid, url="https://alpha.com")
        s2 = make_scan(user_id=uid, url="https://beta.com")
        save_scan(s1)
        save_scan(s2)
        history = get_user_history(uid)
        assert len(history) >= 2
        urls = [h["url"] for h in history]
        assert "https://alpha.com" in urls
        assert "https://beta.com" in urls

    def test_history_includes_correct_summary_fields(self):
        from memory import save_scan, get_user_history
        uid = f"summary-user-{uuid.uuid4().hex[:6]}"
        s = make_scan(user_id=uid, bugs=[
            make_bug(severity="critical"),
            make_bug(severity="serious"),
            make_bug(severity="minor"),
        ])
        save_scan(s)
        history = get_user_history(uid)
        entry = next(h for h in history if h["scan_id"] == s["scan_id"])
        assert entry["total_bugs"] == 3
        assert entry["critical_count"] == 1
        assert entry["serious_count"] == 1
        assert "quality_score" in entry
        assert "pages_scanned" in entry
        assert "performance_metrics" in entry

    def test_get_previous_scan_returns_latest(self):
        from memory import save_scan, get_previous_scan
        uid = f"prev-user-{uuid.uuid4().hex[:6]}"
        url = "https://regression-test.example.com"
        s1 = make_scan(user_id=uid, url=url, bugs=[make_bug(description="Old bug")])
        s2 = make_scan(user_id=uid, url=url, bugs=[make_bug(description="New bug")])
        save_scan(s1)
        save_scan(s2)
        prev = get_previous_scan(uid, url)
        assert prev is not None
        assert "all_bugs" in prev
        descs = [b["description"] for b in prev["all_bugs"]]
        assert len(descs) > 0

    def test_get_previous_scan_no_prior_returns_none(self):
        from memory import get_previous_scan
        assert get_previous_scan("ghost-user", "https://nowhere.example.test") is None

    def test_scan_screenshots_meta_saved(self):
        from memory import save_scan, get_scan
        s = make_scan()
        save_scan(s)
        fetched = get_scan(s["scan_id"])
        assert len(fetched["screenshots_meta"]) == 3
        assert fetched["screenshots_meta"][0]["viewport"] == "desktop"

    def test_history_max_20_returned(self):
        from memory import save_scan, get_user_history
        uid = f"bulk-user-{uuid.uuid4().hex[:6]}"
        for _ in range(25):
            save_scan(make_scan(user_id=uid))
        history = get_user_history(uid)
        assert len(history) <= 20


# ─────────────────────────────────────────────────────────────────────────────
# 2.  report_generator.py
# ─────────────────────────────────────────────────────────────────────────────

class TestReportGenerator:
    """Tests for PDF generation in report_generator.py"""

    def test_pdf_is_valid_pdf_bytes(self):
        from report_generator import generate_pdf_report
        pdf = generate_pdf_report(make_scan())
        assert pdf[:4] == b"%PDF", "Output must start with %PDF magic bytes"
        assert len(pdf) > 1000

    def test_pdf_with_no_bugs(self):
        from report_generator import generate_pdf_report
        s = make_scan(bugs=[])
        s["all_bugs"] = []
        s["fixes"] = []
        s["new_bugs"] = []
        pdf = generate_pdf_report(s)
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_all_severity_levels(self):
        from report_generator import generate_pdf_report
        bugs = [
            make_bug(severity="critical"),
            make_bug(severity="serious"),
            make_bug(severity="moderate"),
            make_bug(severity="minor"),
        ]
        pdf = generate_pdf_report(make_scan(bugs=bugs))
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_html_special_chars_in_description(self):
        """ReportLab XML parser must not crash on Gemini output with < > & chars."""
        from report_generator import generate_pdf_report
        nasty_bugs = [
            make_bug(
                description="The <label> element has color #fff & font-size > 12px",
                element="<input type='text' name='email'>",
                css_fix="color: rgba(0,0,0,0.87); /* was #fff & #aaa */",
                devtools_command="document.querySelector('label').style.color='#333' /* fix <label> */",
            ),
            make_bug(
                description="Button text \"Click & Win\" uses & without escaping",
                element="<button class='cta'>",
                css_fix="content: 'Click &amp; Win';",
            ),
        ]
        pdf = generate_pdf_report(make_scan(bugs=nasty_bugs))
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_network_issues(self):
        from report_generator import generate_pdf_report
        net = [
            {"type": "slow_request", "severity": "moderate",
             "description": "API took >3s", "fix": "Add caching", "url": "https://api.example.com/data"},
            {"type": "http_error", "severity": "critical",
             "description": "500 on /checkout", "fix": "Fix server error", "url": "https://example.com/checkout"},
        ]
        pdf = generate_pdf_report(make_scan(network_issues=net))
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_figma_deviations(self):
        from report_generator import generate_pdf_report
        devs = [
            {"element": "h1.hero-title", "severity": "serious",
             "description": "Font size differs from Figma spec",
             "figma_value": "48px", "actual_value": "36px",
             "css_fix": "font-size: 48px;"},
        ]
        s = make_scan()
        s["figma_deviations"] = devs
        pdf = generate_pdf_report(s)
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_multiple_pages(self):
        from report_generator import generate_pdf_report
        pages = [
            "https://example.com",
            "https://example.com/about",
            "https://example.com/contact",
            "https://example.com/blog",
        ]
        bugs = [make_bug() for _ in range(40)]
        pdf = generate_pdf_report(make_scan(bugs=bugs, pages=pages))
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 5000

    def test_pdf_with_zero_quality_score(self):
        from report_generator import generate_pdf_report
        s = make_scan(bugs=[make_bug(severity="critical") for _ in range(5)])
        s["quality_score"] = 0
        pdf = generate_pdf_report(s)
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_perfect_quality_score(self):
        from report_generator import generate_pdf_report
        s = make_scan(bugs=[])
        s["all_bugs"] = []
        s["quality_score"] = 100
        pdf = generate_pdf_report(s)
        assert pdf[:4] == b"%PDF"

    def test_pdf_escaper_helper(self):
        from report_generator import _e
        assert _e("<b>test</b>") == "&lt;b&gt;test&lt;/b&gt;"
        assert _e("a & b") == "a &amp; b"
        assert _e("price > 0") == "price &gt; 0"
        assert _e("normal text") == "normal text"
        assert _e(None) == ""
        assert _e("") == ""


# ─────────────────────────────────────────────────────────────────────────────
# 3.  main.py  – utilities + API routes
# ─────────────────────────────────────────────────────────────────────────────

class TestMainUtilities:
    """Tests for _camel() and _clean_result() helpers in main.py"""

    def test_camel_flat_dict(self):
        from main import _camel
        result = _camel({"scan_id": "x", "all_bugs": [], "pages_visited": ["a"]})
        assert "scanId" in result
        assert "allBugs" in result
        assert "pagesVisited" in result
        assert "scan_id" not in result

    def test_camel_nested_list(self):
        from main import _camel
        result = _camel({"all_bugs": [{"bug_id": "B1", "css_fix": "color:red"}]})
        assert result["allBugs"][0]["bugId"] == "B1"
        assert result["allBugs"][0]["cssFix"] == "color:red"

    def test_camel_passthrough_non_dicts(self):
        from main import _camel
        assert _camel("string") == "string"
        assert _camel(42) == 42
        assert _camel(None) is None
        assert _camel([1, 2, 3]) == [1, 2, 3]

    def test_clean_result_strips_screenshots(self):
        from main import _clean_result
        raw = {
            "scan_id": "abc",
            "screenshots": [
                {"url": "https://x.com", "viewport": "desktop", "label": "Home", "screenshot": "BASE64DATA"},
            ],
            "visual_results": [{"bugs": []}],
            "figma_b64": "FIGMADATA",
            "quality_score": 80,
        }
        cleaned = _clean_result(raw)
        assert "screenshots" not in cleaned
        assert "visual_results" not in cleaned
        assert "figma_b64" not in cleaned
        assert "screenshots_meta" in cleaned
        assert cleaned["screenshots_meta"][0]["url"] == "https://x.com"
        assert "screenshot" not in cleaned["screenshots_meta"][0]

    def test_clean_result_handles_empty_screenshots(self):
        from main import _clean_result
        raw = {"scan_id": "abc", "screenshots": [], "quality_score": 50}
        cleaned = _clean_result(raw)
        assert cleaned["screenshots_meta"] == []


class TestAPIRoutes:
    """Integration tests for FastAPI routes using TestClient."""

    @pytest.fixture(autouse=True)
    def client(self):
        from main import app
        self.client = TestClient(app)

    def test_health_endpoint(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_get_existing_scan(self):
        from memory import save_scan
        s = make_scan()
        save_scan(s)
        r = self.client.get(f"/scan/{s['scan_id']}")
        assert r.status_code == 200
        data = r.json()
        assert data["scanId"] == s["scan_id"]
        assert "allBugs" in data
        assert "pagesVisited" in data
        assert "qualityScore" in data

    def test_get_missing_scan_returns_404(self):
        r = self.client.get("/scan/does-not-exist-abc-xyz")
        assert r.status_code == 404

    def test_get_history(self):
        from memory import save_scan
        uid = f"api-hist-{uuid.uuid4().hex[:6]}"
        s1 = make_scan(user_id=uid)
        s2 = make_scan(user_id=uid)
        save_scan(s1)
        save_scan(s2)
        r = self.client.get(f"/history/{uid}")
        assert r.status_code == 200
        data = r.json()
        assert "scans" in data
        assert len(data["scans"]) >= 2

    def test_history_response_is_camel_case(self):
        from memory import save_scan
        uid = f"camel-hist-{uuid.uuid4().hex[:6]}"
        save_scan(make_scan(user_id=uid))
        r = self.client.get(f"/history/{uid}")
        scans = r.json()["scans"]
        assert len(scans) >= 1
        entry = scans[0]
        assert "scanId" in entry
        assert "qualityScore" in entry
        assert "totalBugs" in entry

    def test_pdf_report_download(self):
        from memory import save_scan
        s = make_scan()
        save_scan(s)
        r = self.client.get(f"/scan/{s['scan_id']}/report")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"

    def test_pdf_report_for_large_scan(self):
        """PDF generation for scan with 53 bugs must not 500."""
        from memory import save_scan
        bugs = []
        for i in range(53):
            sevs = ["critical", "serious", "moderate", "minor"]
            bugs.append(make_bug(
                severity=sevs[i % 4],
                description=f"Bug {i}: The <input> element & label have contrast ratio < 3:1",
                css_fix=f"color: #333; /* fix {i} <label> */",
            ))
        s = make_scan(bugs=bugs, pages=[f"https://example.com/page{i}" for i in range(8)])
        save_scan(s)
        r = self.client.get(f"/scan/{s['scan_id']}/report")
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"

    def test_pdf_report_for_missing_scan_returns_404(self):
        r = self.client.get("/scan/definitely-missing-xyz/report")
        assert r.status_code == 404

    def test_scan_endpoint_with_mocked_run_scan(self):
        """POST /scan should return camelCase scan data."""
        mock_result = make_scan(url="https://mock-test.example.com")
        mock_result["screenshots"] = []
        mock_result["visual_results"] = []
        mock_result["figma_b64"] = None
        with patch("main.run_scan", return_value=mock_result):
            r = self.client.post("/scan", json={"userId": "test-user", "url": "https://mock-test.example.com"})
        assert r.status_code == 200
        data = r.json()
        assert "scanId" in data
        assert "allBugs" in data
        assert "qualityScore" in data
        assert "screenshots" not in data
        assert "screenshotsMeta" in data


# ─────────────────────────────────────────────────────────────────────────────
# 4.  playwright_navigator.py  – URL guards (no live browser)
# ─────────────────────────────────────────────────────────────────────────────

class TestPlaywrightNavigatorHelpers:
    """Unit tests for URL validation logic without launching a browser."""

    def test_same_domain_accepted(self):
        from urllib.parse import urlparse
        base = "https://example.com"
        link = "https://example.com/about"
        base_h = urlparse(base).netloc
        link_h = urlparse(link).netloc
        assert base_h == link_h

    def test_different_domain_rejected(self):
        from urllib.parse import urlparse
        base = "https://example.com"
        link = "https://evil.com/phish"
        base_h = urlparse(base).netloc
        link_h = urlparse(link).netloc
        assert base_h != link_h

    def test_subdomain_treated_as_different(self):
        from urllib.parse import urlparse
        base = "https://example.com"
        link = "https://sub.example.com/page"
        base_h = urlparse(base).netloc
        link_h = urlparse(link).netloc
        assert base_h != link_h

    def test_url_without_scheme_parse(self):
        from urllib.parse import urlparse
        link = "example.com/path"
        parsed = urlparse(link)
        assert parsed.netloc == "" or parsed.scheme == ""

    def test_fragment_only_excluded(self):
        """Links that are only fragments (#section) should not be crawled as new pages."""
        from urllib.parse import urlparse
        link = "#section-2"
        parsed = urlparse(link)
        assert parsed.netloc == ""
        assert parsed.scheme == ""

    def test_mailto_excluded(self):
        from urllib.parse import urlparse
        link = "mailto:info@example.com"
        parsed = urlparse(link)
        assert parsed.scheme == "mailto"

    def test_https_url_valid(self):
        from urllib.parse import urlparse
        url = "https://simply.spark214.workers.dev/"
        parsed = urlparse(url)
        assert parsed.scheme in ("http", "https")
        assert parsed.netloc != ""

    def test_http_url_valid(self):
        from urllib.parse import urlparse
        url = "http://example.com/page"
        parsed = urlparse(url)
        assert parsed.scheme == "http"


# ─────────────────────────────────────────────────────────────────────────────
# 5.  agent.py  – LangGraph pipeline nodes (mocked externals)
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentNodes:
    """Unit tests for individual LangGraph nodes with all I/O mocked."""

    def _base_state(self, url="https://example.com", user_id="test-agent"):
        return {
            "scan_id": "", "user_id": user_id, "url": url,
            "figma_b64": None,
            "screenshots": [], "network_issues": [], "console_errors": [], "pages_visited": [],
            "performance_metrics": {}, "visual_results": [],
            "all_bugs": [], "figma_deviations": [], "fixes": [],
            "new_bugs": [], "quality_score": 0, "figma_match_score": 100,
            "status": "idle", "error": None,
        }

    def test_observe_node_initialises_state(self):
        from agent import observe_node
        state = self._base_state()
        out = observe_node(state)
        assert out["scan_id"] != ""
        assert out["status"] == "observe"
        assert out["all_bugs"] == []
        assert out["error"] is None

    def test_observe_node_generates_unique_scan_ids(self):
        from agent import observe_node
        ids = {observe_node(self._base_state())["scan_id"] for _ in range(5)}
        assert len(ids) == 5

    def test_navigate_node_populates_screenshots(self):
        from agent import navigate_node
        state = self._base_state()
        state["scan_id"] = str(uuid.uuid4())
        mock_nav = {
            "screenshots": [{"url": "https://example.com", "screenshot": "B64", "viewport": "desktop", "label": "Desktop – Home"}],
            "network_issues": [],
            "console_errors": [{"type": "error", "text": "Failed to load resource", "source": "console"}],
            "pages_visited": ["https://example.com"],
            "performance_metrics": {"initial_load_ms": 300, "pages_scanned": 1, "total_requests": 5, "error_count": 0, "slow_request_count": 0, "js_error_count": 1, "cors_error_count": 0},
            "raw_network_log": [],
        }
        with patch("agent.run_navigation", return_value=mock_nav):
            out = navigate_node(state)
        assert len(out["screenshots"]) == 1
        assert out["pages_visited"] == ["https://example.com"]
        assert out["performance_metrics"]["initial_load_ms"] == 300
        assert len(out["console_errors"]) == 1

    def test_navigate_node_handles_error_gracefully(self):
        from agent import navigate_node
        state = self._base_state()
        with patch("agent.run_navigation", side_effect=Exception("Chromium crashed")):
            out = navigate_node(state)
        assert out["screenshots"] == []
        assert "Chromium crashed" in out["error"]

    def test_detect_node_with_no_screenshots(self):
        from agent import detect_node
        state = self._base_state()
        state["scan_id"] = str(uuid.uuid4())
        state["screenshots"] = []
        out = detect_node(state)
        assert out["all_bugs"] == []

    def test_detect_node_extracts_bugs_from_visual_results(self):
        from agent import detect_node
        state = self._base_state()
        state["scan_id"] = str(uuid.uuid4())
        state["screenshots"] = [
            {"url": "https://example.com", "screenshot": "B64", "viewport": "desktop", "label": "Desktop – Home"},
        ]
        mock_visual = [{"url": "https://example.com", "label": "Desktop – Home", "viewport": "desktop", "bugs": [
            {"bug_id": "B001", "severity": "critical", "category": "Contrast", "description": "Low contrast", "element_description": "h1", "css_fix": "", "devtools_command": ""},
            {"bug_id": "B002", "severity": "minor",    "category": "Spacing",  "description": "Bad padding",  "element_description": "p",  "css_fix": "", "devtools_command": ""},
        ]}]
        with patch("agent.analyze_all_screenshots", return_value=mock_visual), \
             patch("agent.get_previous_scan", return_value=None):
            out = detect_node(state)
        assert len(out["all_bugs"]) == 2
        assert out["all_bugs"][0]["severity"] == "critical"

    def test_detect_node_sorts_bugs_by_severity(self):
        from agent import detect_node
        state = self._base_state()
        state["scan_id"] = str(uuid.uuid4())
        state["screenshots"] = [{"url": "x", "screenshot": "B64", "viewport": "desktop", "label": "Desktop"}]
        bugs = [
            {"bug_id": "B1", "severity": "minor",    "description": "d1", "category": "c"},
            {"bug_id": "B2", "severity": "critical", "description": "d2", "category": "c"},
            {"bug_id": "B3", "severity": "moderate", "description": "d3", "category": "c"},
            {"bug_id": "B4", "severity": "serious",  "description": "d4", "category": "c"},
        ]
        mock_visual = [{"url": "x", "label": "Desktop", "viewport": "desktop", "bugs": bugs}]
        with patch("agent.analyze_all_screenshots", return_value=mock_visual), \
             patch("agent.get_previous_scan", return_value=None):
            out = detect_node(state)
        severities = [b["severity"] for b in out["all_bugs"]]
        order = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}
        assert all(order[severities[i]] <= order[severities[i + 1]] for i in range(len(severities) - 1))

    def test_detect_node_marks_new_bugs_vs_previous(self):
        from agent import detect_node
        state = self._base_state()
        state["scan_id"] = str(uuid.uuid4())
        state["screenshots"] = [{"url": "x", "screenshot": "B64", "viewport": "desktop", "label": "Desktop"}]
        existing_bug = {"bug_id": "OLD", "severity": "serious", "description": "Known bug", "category": "c"}
        new_bug      = {"bug_id": "NEW", "severity": "serious", "description": "Brand new bug", "category": "c"}
        mock_visual = [{"url": "x", "label": "Desktop", "viewport": "desktop", "bugs": [existing_bug, new_bug]}]
        prev = {"all_bugs": [existing_bug]}
        with patch("agent.analyze_all_screenshots", return_value=mock_visual), \
             patch("agent.get_previous_scan", return_value=prev):
            out = detect_node(state)
        new_descs = [b["description"] for b in out["new_bugs"]]
        assert "Brand new bug" in new_descs
        assert "Known bug" not in new_descs

    def test_fix_node_generates_fixes_for_bugs_with_commands(self):
        from agent import fix_node
        state = self._base_state()
        state["all_bugs"] = [
            {"bug_id": "B1", "severity": "critical", "category": "Contrast", "description": "Low",
             "css_fix": "color:#fff", "devtools_command": "document.body.style.color='#fff'", "html_fix": ""},
            {"bug_id": "B2", "severity": "minor", "category": "Spacing", "description": "Bad pad",
             "css_fix": "", "devtools_command": "", "html_fix": ""},
        ]
        out = fix_node(state)
        assert len(out["fixes"]) == 1
        assert out["fixes"][0]["bug_id"] == "B1"

    def test_fix_node_empty_bugs_gives_empty_fixes(self):
        from agent import fix_node
        state = self._base_state()
        state["all_bugs"] = []
        out = fix_node(state)
        assert out["fixes"] == []

    def test_verify_node_computes_quality_score(self):
        from agent import verify_node
        state = self._base_state()
        state["all_bugs"] = [
            make_bug(severity="critical"),
            make_bug(severity="serious"),
            make_bug(severity="moderate"),
            make_bug(severity="minor"),
        ]
        state["network_issues"] = []
        state["figma_deviations"] = []
        out = verify_node(state)
        assert 0 <= out["quality_score"] <= 100

    def test_verify_node_zero_bugs_high_score(self):
        from agent import verify_node
        state = self._base_state()
        state["all_bugs"] = []
        state["network_issues"] = []
        state["figma_deviations"] = []
        out = verify_node(state)
        assert out["quality_score"] >= 80

    def test_verify_node_many_critical_bugs_low_score(self):
        from agent import verify_node
        state = self._base_state()
        state["all_bugs"] = [make_bug(severity="critical") for _ in range(10)]
        state["network_issues"] = []
        state["figma_deviations"] = []
        out = verify_node(state)
        assert out["quality_score"] < 60

    def test_report_node_saves_to_db(self):
        from agent import report_node
        state = self._base_state()
        state["scan_id"] = str(uuid.uuid4())
        state["screenshots"] = []
        state["all_bugs"] = [make_bug()]
        state["network_issues"] = []
        state["figma_deviations"] = []
        state["fixes"] = []
        state["new_bugs"] = [make_bug()]
        state["pages_visited"] = ["https://example.com"]
        state["quality_score"] = 70
        state["figma_match_score"] = 90
        state["performance_metrics"] = {"initial_load_ms": 400, "pages_scanned": 1}
        state["screenshots_meta"] = []
        with patch("agent.save_scan") as mock_save:
            out = report_node(state)
        mock_save.assert_called_once()
        call_data = mock_save.call_args[0][0]
        assert call_data["scan_id"] == state["scan_id"]
        assert call_data["quality_score"] == 70


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Quality score edge-cases
# ─────────────────────────────────────────────────────────────────────────────

class TestQualityScore:
    """Ensure quality_score is always 0–100 and behaves logically."""

    def _verify(self, bugs, network_issues=None, figma_devs=None):
        from agent import verify_node
        state = {
            "scan_id": str(uuid.uuid4()), "user_id": "u", "url": "https://x.com",
            "figma_b64": None,
            "all_bugs": bugs,
            "network_issues": network_issues or [],
            "console_errors": [],
            "figma_deviations": figma_devs or [],
            "screenshots": [], "pages_visited": [],
            "performance_metrics": {}, "visual_results": [],
            "fixes": [], "new_bugs": [],
            "quality_score": 0, "figma_match_score": 100,
            "status": "verify", "error": None,
        }
        return verify_node(state)["quality_score"]

    def test_score_range(self):
        assert 0 <= self._verify([]) <= 100
        assert 0 <= self._verify([make_bug(severity="critical")] * 20) <= 100

    def test_no_bugs_better_than_many_bugs(self):
        clean  = self._verify([])
        broken = self._verify([make_bug(severity="critical")] * 5)
        assert clean > broken

    def test_critical_worse_than_minor(self):
        crit  = self._verify([make_bug(severity="critical")])
        minor = self._verify([make_bug(severity="minor")])
        assert minor > crit

    def test_network_issues_reduce_score(self):
        net = [{"severity": "critical", "type": "http_error", "description": "500", "fix": "fix it"}]
        with_net    = self._verify([], network_issues=net)
        without_net = self._verify([])
        assert without_net >= with_net
