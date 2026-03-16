import os
import base64
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

FIGMA_COMPARE_PROMPT = """You are a pixel-perfect design QA specialist. You are given TWO images:
- Image 1: The Figma design mockup (the intended design)
- Image 2: The actual built application screenshot

Compare them carefully and identify ALL design deviations. Look for:
- Colors that don't match the design
- Wrong font sizes, weights, or families
- Spacing/padding/margin differences
- Missing elements from the design
- Extra elements not in the design  
- Wrong component variants used
- Alignment differences
- Size/proportion differences
- Icon or image differences

Respond in this exact JSON format:
{
  "deviations": [
    {
      "deviation_id": "DEV_001",
      "severity": "critical|serious|moderate|minor",
      "element": "describe which element",
      "figma_value": "what it looks like in the design",
      "actual_value": "what it looks like in the app",
      "description": "clear description of the deviation",
      "css_fix": "CSS to match the design",
      "devtools_command": "JavaScript to fix in browser console"
    }
  ],
  "design_match_score": 0-100,
  "summary": "overall design fidelity summary"
}

Return ONLY valid JSON."""


def compare_with_figma(screenshot_b64: str, figma_b64: str) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"deviations": [], "design_match_score": 100, "summary": "No API key"}

    try:
        client = genai.Client(api_key=api_key)

        screenshot_bytes = base64.b64decode(screenshot_b64)
        figma_bytes = base64.b64decode(figma_b64)

        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                "Image 1 - Figma Design Mockup:",
                types.Part.from_bytes(data=figma_bytes, mime_type="image/png"),
                "Image 2 - Actual Application Screenshot:",
                types.Part.from_bytes(data=screenshot_bytes, mime_type="image/png"),
                FIGMA_COMPARE_PROMPT,
            ],
        )

        text = (response.text or "").strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        import json
        return json.loads(text)

    except Exception as e:
        print(f"Figma compare error: {e}")
        return {
            "deviations": [],
            "design_match_score": 0,
            "summary": f"Comparison error: {str(e)[:100]}",
        }
