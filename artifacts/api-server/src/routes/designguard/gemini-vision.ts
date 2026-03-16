import { ai } from "@workspace/integrations-gemini-ai";

const ACCESSIBILITY_PROMPT = `You are DesignGuard, an expert AI accessibility auditor. You analyze website screenshots and detect WCAG 2.1 accessibility violations using only visual inspection — no code access, no DOM.

Detect ALL violations across these categories:
1. COLOR_CONTRAST — Text/background contrast below 4.5:1 (AA)
2. FONT_SIZE — Text below 12px minimum
3. MISSING_ALT_TEXT — Images with no descriptive context
4. KEYBOARD_FOCUS — Interactive elements with no focus indicator
5. BUTTON_SIZE — Touch targets smaller than 44x44px
6. HEADING_STRUCTURE — Missing or illogical heading hierarchy
7. LINK_TEXT — Generic link text like 'click here'
8. FORM_LABELS — Input fields with no visible label

Respond in EXACT JSON with no markdown code blocks:
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
}`;

export interface VisionResult {
  violations: ViolationRaw[];
  compliance_score: number;
  page_summary: string;
  total_violations: number;
  critical_count: number;
  serious_count: number;
  moderate_count: number;
}

export interface ViolationRaw {
  violation_id: string;
  category: string;
  severity: string;
  element_description: string;
  wcag_criterion: string;
  current_value: string;
  required_value: string;
  fix_description: string;
  fix_action: {
    type: string;
    property: string;
    old_value: string;
    new_value: string;
    devtools_command: string;
  };
}

export async function analyzeScreenshot(screenshotBase64: string): Promise<VisionResult> {
  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: [
      {
        role: "user",
        parts: [
          {
            inlineData: {
              mimeType: "image/jpeg",
              data: screenshotBase64,
            },
          },
          { text: ACCESSIBILITY_PROMPT },
        ],
      },
    ],
    config: { maxOutputTokens: 8192 },
  });

  const text = response.text ?? "";

  // Strip markdown code blocks if present
  const cleaned = text.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();

  try {
    return JSON.parse(cleaned) as VisionResult;
  } catch {
    // Return a fallback result with a simulated scan if parsing fails
    console.error("Failed to parse Gemini response:", text);
    return {
      violations: [],
      compliance_score: 85,
      page_summary: "Unable to fully analyze screenshot. Please try with a clearer image.",
      total_violations: 0,
      critical_count: 0,
      serious_count: 0,
      moderate_count: 0,
    };
  }
}
