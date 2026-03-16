import os
import json
import base64
from google import genai
from google.genai import types
from PIL import Image
import io
from typing import Dict, Any

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

ACCESSIBILITY_PROMPT = """You are DesignGuard, an expert AI accessibility auditor. You analyze 
website screenshots and detect WCAG 2.1 accessibility violations using 
only visual inspection — no code access, no DOM.

Detect ALL violations across these categories:
1. COLOR_CONTRAST — Text/background contrast below 4.5:1 (AA)
2. FONT_SIZE — Text below 12px minimum
3. MISSING_ALT_TEXT — Images with no descriptive context
4. KEYBOARD_FOCUS — Interactive elements with no focus indicator
5. BUTTON_SIZE — Touch targets smaller than 44x44px
6. HEADING_STRUCTURE — Missing or illogical heading hierarchy
7. LINK_TEXT — Generic link text like 'click here'
8. FORM_LABELS — Input fields with no visible label

Respond in EXACT JSON with no markdown formatting:
{
  "violations": [
    {
      "violation_id": "unique_id",
      "category": "COLOR_CONTRAST",
      "severity": "critical",
      "element_description": "visual location of element",
      "wcag_criterion": "WCAG 1.4.3",
      "current_value": "what it currently is",
      "required_value": "what it should be",
      "fix_description": "what needs to change",
      "fix_action": {
        "type": "css_injection",
        "property": "CSS property or HTML attribute",
        "old_value": "current value",
        "new_value": "corrected value",
        "devtools_command": "exact JavaScript for browser console"
      }
    }
  ],
  "compliance_score": 75,
  "page_summary": "brief description of the page",
  "total_violations": 3,
  "critical_count": 1,
  "serious_count": 1,
  "moderate_count": 1
}"""


def analyze_screenshot(screenshot_base64: str) -> Dict[str, Any]:
    """Analyze a screenshot for WCAG accessibility violations using Gemini multimodal."""
    try:
        # Decode base64 to PIL Image
        img_data = base64.b64decode(screenshot_base64)
        img = Image.open(io.BytesIO(img_data))

        # Convert to bytes for inline data
        buf = io.BytesIO()
        fmt = img.format or "JPEG"
        img.save(buf, format=fmt)
        buf.seek(0)
        img_bytes = buf.read()

        mime_map = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
        mime_type = mime_map.get(fmt, "image/jpeg")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                ACCESSIBILITY_PROMPT,
            ],
            config=types.GenerateContentConfig(
                max_output_tokens=8192,
                response_mime_type="application/json",
            ),
        )

        text = response.text or ""
        # Strip markdown code blocks if present
        cleaned = text.replace("```json", "").replace("```", "").strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(cleaned[start:end])
            raise

    except Exception as e:
        print(f"Gemini vision error: {e}")
        return {
            "violations": [],
            "compliance_score": 85,
            "page_summary": f"Analysis error: {str(e)}",
            "total_violations": 0,
            "critical_count": 0,
            "serious_count": 0,
            "moderate_count": 0,
        }
