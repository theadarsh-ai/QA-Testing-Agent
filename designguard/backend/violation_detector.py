from typing import List, Dict, Any
from models import Violation, FixAction


SEVERITY_ORDER = {"critical": 0, "serious": 1, "moderate": 2}

WCAG_CRITERIA = {
    "COLOR_CONTRAST": "WCAG 1.4.3",
    "FONT_SIZE": "WCAG 1.4.4",
    "MISSING_ALT_TEXT": "WCAG 1.1.1",
    "KEYBOARD_FOCUS": "WCAG 2.4.7",
    "BUTTON_SIZE": "WCAG 2.5.5",
    "HEADING_STRUCTURE": "WCAG 1.3.1",
    "LINK_TEXT": "WCAG 2.4.4",
    "FORM_LABELS": "WCAG 1.3.1",
}


def classify_violations(raw_violations: List[Dict[str, Any]]) -> List[Violation]:
    """Parse and classify raw violations from Gemini response."""
    violations = []
    for v in raw_violations:
        fix_action_data = v.get("fix_action")
        fix_action = None
        if fix_action_data:
            fix_action = FixAction(
                type=fix_action_data.get("type", "devtools_command"),
                property=fix_action_data.get("property"),
                old_value=fix_action_data.get("old_value"),
                new_value=fix_action_data.get("new_value"),
                devtools_command=fix_action_data.get("devtools_command", "// No command generated"),
            )

        violation = Violation(
            violation_id=v.get("violation_id", f"v_{len(violations)+1}"),
            category=v.get("category", "UNKNOWN"),
            severity=v.get("severity", "moderate"),
            element_description=v.get("element_description", "Unknown element"),
            wcag_criterion=v.get("wcag_criterion", WCAG_CRITERIA.get(v.get("category", ""), "WCAG 2.1")),
            current_value=v.get("current_value"),
            required_value=v.get("required_value"),
            fix_description=v.get("fix_description", "Apply accessibility fix"),
            fix_action=fix_action,
        )
        violations.append(violation)
    return violations


def prioritize_violations(violations: List[Violation], max_count: int = 10) -> List[Violation]:
    """Sort violations by severity (critical first) and return top N."""
    sorted_violations = sorted(
        violations,
        key=lambda v: SEVERITY_ORDER.get(v.severity, 3)
    )
    return sorted_violations[:max_count]
