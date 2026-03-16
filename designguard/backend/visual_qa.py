import os
import time
import json
import base64
from typing import List, Dict, Any
from google import genai
from google.genai import types


VISUAL_QA_PROMPT = """You are a senior QA engineer with expertise in both frontend UX and backend integration issues. Analyze this screenshot and identify ALL quality issues — including visual bugs AND backend/API problems visible in the UI.

Report issues across these categories:

FRONTEND / VISUAL:
1. LAYOUT_BUG — broken layout, overlapping elements, elements cut off, wrong positioning
2. TEXT_OVERFLOW — text overflowing its container, truncated text, text outside bounds
3. FONT_INCONSISTENCY — inconsistent font sizes, weights, or families across similar elements
4. COLOR_INCONSISTENCY — mismatched colors, wrong brand colors, poor contrast
5. MISALIGNMENT — elements not aligned to grid, uneven spacing, inconsistent padding/margins
6. MISSING_IMAGE — broken image placeholder, alt text visible, empty image containers
7. RESPONSIVE_ISSUE — layout breaking at this viewport, elements too small to tap, horizontal scroll
8. WCAG_VIOLATION — contrast ratio below 4.5:1, missing alt text, missing focus indicators, form label issues
9. DESIGN_DEVIATION — element doesn't match expected design, wrong size/shape/style

BACKEND / INTEGRATION:
10. ERROR_STATE — visible error messages, 404/500 error pages, "Something went wrong", crash screens, stack traces shown to users
11. BROKEN_API — data not loading, empty lists/tables where data should appear, "undefined" or "[object Object]" text rendered on screen, NaN values, missing dynamic content
12. AUTH_FAILURE — "Unauthorized", "Please log in", unexpected redirects to login, session expiry shown, 401/403 UI
13. LOADING_STUCK — loading spinners, skeleton screens, or progress bars that never resolved (page appears to have finished loading but spinner still shows)
14. FORM_BROKEN — form submission failures, validation errors not shown, form fields not responding, submit button disabled with no explanation
15. CONSOLE_ERROR_VISIBLE — error banners, toast notifications showing error messages, debug output rendered in production UI
16. MISSING_CONTENT — sections that appear empty but should have content (empty product grids, empty user profiles, blank chart areas, empty dashboards)
17. API_DATA_STALE — timestamps far in the past, "Last updated: never", outdated data placeholders

For EACH issue found, respond with this exact JSON format:
{
  "bugs": [
    {
      "bug_id": "BUG_001",
      "category": "LAYOUT_BUG",
      "severity": "critical|serious|moderate|minor",
      "element_description": "describe exactly what element has the issue",
      "location_on_screen": "top-left|top-center|top-right|middle-left|center|middle-right|bottom-left|bottom-center|bottom-right",
      "description": "clear description of the bug — for backend issues explain what API/data problem is causing it",
      "css_fix": "exact CSS property: value; to fix it, or null for backend issues",
      "html_fix": "any HTML change needed, or null",
      "devtools_command": "document.querySelector('selector').style.property = 'value' for frontend fixes; console command to debug backend issue if applicable",
      "wcag_criterion": "WCAG criterion if applicable, or null"
    }
  ],
  "page_quality_score": 0-100,
  "viewport": "desktop|tablet|mobile",
  "summary": "one sentence summary of overall quality including both visual and backend issues"
}

Severity guide:
- critical: blocks users entirely (page crash, auth failure, broken form, 500 error page)
- serious: major UX problem (broken API data, missing content, stuck loading)
- moderate: noticeable but users can work around it
- minor: polish/cosmetic issue

A high-quality page with no issues scores 85+. Backend errors score below 50. If no bugs found, return empty bugs array with score 95.
Return ONLY valid JSON, no markdown."""


def _build_prompt(viewport: str, page_label: str, console_errors: List[Dict], network_issues: List[Dict]) -> str:
    parts = []
    if page_label:
        parts.append(f"Page: {page_label}")
    if viewport:
        parts.append(f"Viewport: {viewport}")

    if console_errors:
        err_texts = [f"  - [{e.get('type','error')}] {e.get('text','')}" for e in console_errors[:5]]
        parts.append("Browser Console Errors detected on this page:\n" + "\n".join(err_texts))

    if network_issues:
        net_texts = [f"  - [{n.get('type','error')} {n.get('status_code','')}] {n.get('description','')}" for n in network_issues[:5]]
        parts.append("Network Issues detected on this page:\n" + "\n".join(net_texts))

    if parts:
        return "\n".join(parts) + "\n\n" + VISUAL_QA_PROMPT
    return VISUAL_QA_PROMPT


def _call_gemini_with_retry(client, screenshot_b64: str, prompt: str, max_retries: int = 3) -> str:
    img_bytes = base64.b64decode(screenshot_b64)
    last_err = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    prompt,
                ],
            )
            return response.text or ""
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait = 35 * (attempt + 1)
                print(f"Gemini rate limit hit, waiting {wait}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait)
            else:
                raise
    raise last_err


def analyze_screenshot(
    screenshot_b64: str,
    viewport: str = "desktop",
    page_label: str = "",
    console_errors: List[Dict] = None,
    network_issues: List[Dict] = None,
) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"bugs": [], "page_quality_score": 50, "viewport": viewport, "summary": "No API key configured"}

    try:
        client = genai.Client(api_key=api_key)
        prompt = _build_prompt(
            viewport=viewport,
            page_label=page_label,
            console_errors=console_errors or [],
            network_issues=network_issues or [],
        )

        text = _call_gemini_with_retry(client, screenshot_b64, prompt)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        result = json.loads(text)
        result["viewport"] = viewport
        return result

    except Exception as e:
        print(f"Visual QA error: {e}")
        return {
            "bugs": [],
            "page_quality_score": 50,
            "viewport": viewport,
            "summary": f"Analysis error: {str(e)[:100]}",
        }


def analyze_all_screenshots(
    screenshots: List[Dict],
    console_errors: List[Dict] = None,
    network_issues: List[Dict] = None,
) -> List[Dict[str, Any]]:
    results = []
    for i, shot in enumerate(screenshots):
        if i > 0:
            time.sleep(1)
        result = analyze_screenshot(
            shot["screenshot"],
            viewport=shot.get("viewport", "desktop"),
            page_label=shot.get("label", ""),
            console_errors=console_errors or [],
            network_issues=network_issues or [],
        )
        result["url"]            = shot.get("url", "")
        result["label"]          = shot.get("label", "")
        result["screenshot_b64"] = shot["screenshot"]
        results.append(result)
    return results
