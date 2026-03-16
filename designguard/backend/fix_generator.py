from typing import Dict
from models import Violation, AppliedFix


FIX_IMPROVEMENTS: Dict[str, int] = {
    "COLOR_CONTRAST": 8,
    "FONT_SIZE": 5,
    "MISSING_ALT_TEXT": 6,
    "KEYBOARD_FOCUS": 7,
    "BUTTON_SIZE": 4,
    "HEADING_STRUCTURE": 5,
    "LINK_TEXT": 4,
    "FORM_LABELS": 6,
}

WCAG_MET: Dict[str, str] = {
    "COLOR_CONTRAST": "WCAG 1.4.3 (Contrast Minimum AA)",
    "FONT_SIZE": "WCAG 1.4.4 (Resize Text)",
    "MISSING_ALT_TEXT": "WCAG 1.1.1 (Non-text Content)",
    "KEYBOARD_FOCUS": "WCAG 2.4.7 (Focus Visible)",
    "BUTTON_SIZE": "WCAG 2.5.5 (Target Size)",
    "HEADING_STRUCTURE": "WCAG 1.3.1 (Info and Relationships)",
    "LINK_TEXT": "WCAG 2.4.4 (Link Purpose)",
    "FORM_LABELS": "WCAG 1.3.1 (Info and Relationships)",
}

FIX_TEMPLATES: Dict[str, str] = {
    "COLOR_CONTRAST": """// Fix color contrast - increase contrast ratio to 4.5:1 minimum (WCAG AA)
document.querySelectorAll('*').forEach(el => {
  const style = window.getComputedStyle(el);
  if (el.childNodes.length > 0) {
    el.style.color = '#1a1a1a';
  }
});
// Target specific element with low contrast:
// document.querySelector('.your-selector').style.color = '#000000';
// document.querySelector('.your-selector').style.backgroundColor = '#ffffff';""",

    "FONT_SIZE": """// Fix font size below 12px minimum (WCAG recommends 16px for body text)
document.querySelectorAll('*').forEach(el => {
  const size = parseFloat(window.getComputedStyle(el).fontSize);
  if (size > 0 && size < 16) {
    el.style.fontSize = '16px';
    el.style.lineHeight = '1.5';
  }
});""",

    "MISSING_ALT_TEXT": """// Fix missing alt text on images (WCAG 1.1.1)
document.querySelectorAll('img:not([alt]), img[alt=""]').forEach((img, i) => {
  // Replace with descriptive text based on context
  img.setAttribute('alt', 'Descriptive image text ' + (i + 1));
});
// For decorative images, use empty alt:
// img.setAttribute('alt', '');
// img.setAttribute('role', 'presentation');""",

    "KEYBOARD_FOCUS": """// Fix missing focus indicators (WCAG 2.4.7)
const focusStyle = document.createElement('style');
focusStyle.textContent = `
  *:focus {
    outline: 3px solid #005FCC !important;
    outline-offset: 2px !important;
  }
  *:focus:not(:focus-visible) {
    outline: none !important;
  }
  *:focus-visible {
    outline: 3px solid #005FCC !important;
    outline-offset: 2px !important;
  }
`;
document.head.appendChild(focusStyle);""",

    "BUTTON_SIZE": """// Fix touch target size - minimum 44x44px (WCAG 2.5.5)
document.querySelectorAll('button, a, [role="button"], input[type="submit"], input[type="button"]').forEach(el => {
  const rect = el.getBoundingClientRect();
  if (rect.width < 44 || rect.height < 44) {
    el.style.minWidth = '44px';
    el.style.minHeight = '44px';
    el.style.display = 'inline-flex';
    el.style.alignItems = 'center';
    el.style.justifyContent = 'center';
    el.style.padding = '8px 16px';
  }
});""",

    "HEADING_STRUCTURE": """// Audit and fix heading hierarchy (WCAG 1.3.1)
const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
console.log('Current heading structure:');
headings.forEach(h => console.log(`  ${h.tagName}: "${h.textContent?.trim().substring(0, 60)}"`));

// Fix: Ensure only one h1, and logical nesting
// Example fix - change an h4 that should be h2:
// document.querySelector('.section-title').outerHTML = 
//   document.querySelector('.section-title').outerHTML.replace('<h4', '<h2').replace('</h4>', '</h2>');""",

    "LINK_TEXT": """// Fix non-descriptive link text (WCAG 2.4.4)
document.querySelectorAll('a').forEach(link => {
  const text = link.textContent?.trim().toLowerCase();
  const genericTexts = ['click here', 'read more', 'here', 'more', 'link', 'this'];
  if (genericTexts.includes(text)) {
    // Add aria-label with descriptive context
    const context = link.closest('p, li, article')?.textContent?.trim().substring(0, 50);
    link.setAttribute('aria-label', `Navigate to: ${context || link.href}`);
    // Or update visible text: link.textContent = 'Read our accessibility documentation';
  }
});""",

    "FORM_LABELS": """// Fix form inputs without labels (WCAG 1.3.1)
document.querySelectorAll('input, select, textarea').forEach((input, i) => {
  const hasLabel = input.id && document.querySelector(`label[for="${input.id}"]`);
  const hasAriaLabel = input.getAttribute('aria-label') || input.getAttribute('aria-labelledby');
  
  if (!hasLabel && !hasAriaLabel) {
    const placeholder = input.getAttribute('placeholder');
    const name = input.getAttribute('name');
    const labelText = placeholder || name || `Field ${i + 1}`;
    input.setAttribute('aria-label', labelText);
    // Better: create a visible label element
    // const label = document.createElement('label');
    // label.textContent = labelText;
    // label.htmlFor = input.id || (input.id = `field-${i}`);
    // input.parentNode.insertBefore(label, input);
  }
});""",
}


def generate_fix_action(violation: Violation) -> AppliedFix:
    """Generate a specific DevTools fix command for a WCAG violation."""
    category = violation.category.upper() if violation.category else "UNKNOWN"

    # Use Gemini-provided command if available, else use template
    if violation.fix_action and violation.fix_action.devtools_command:
        devtools_command = violation.fix_action.devtools_command
    else:
        devtools_command = FIX_TEMPLATES.get(
            category,
            f"// Fix for {violation.category}\n// {violation.fix_description}\n// Apply manually based on element: {violation.element_description}"
        )

    return AppliedFix(
        violation_id=violation.violation_id,
        fix_applied=True,
        devtools_command=devtools_command,
        explanation=violation.fix_description or f"Fix applied for {violation.category}",
        wcag_criterion_met=WCAG_MET.get(category, violation.wcag_criterion or "WCAG 2.1"),
        compliance_improvement=FIX_IMPROVEMENTS.get(category, 3),
    )
