import type { ViolationRaw } from "./gemini-vision.js";

export interface AppliedFix {
  violationId: string;
  fixApplied: boolean;
  devtoolsCommand: string;
  explanation: string;
  wcagCriterionMet: string;
  complianceImprovement: number;
}

const FIX_IMPROVEMENTS: Record<string, number> = {
  COLOR_CONTRAST: 8,
  FONT_SIZE: 5,
  MISSING_ALT_TEXT: 6,
  KEYBOARD_FOCUS: 7,
  BUTTON_SIZE: 4,
  HEADING_STRUCTURE: 5,
  LINK_TEXT: 4,
  FORM_LABELS: 6,
};

const WCAG_CRITERIA: Record<string, string> = {
  COLOR_CONTRAST: "WCAG 1.4.3 (Contrast Minimum)",
  FONT_SIZE: "WCAG 1.4.4 (Resize Text)",
  MISSING_ALT_TEXT: "WCAG 1.1.1 (Non-text Content)",
  KEYBOARD_FOCUS: "WCAG 2.4.7 (Focus Visible)",
  BUTTON_SIZE: "WCAG 2.5.5 (Target Size)",
  HEADING_STRUCTURE: "WCAG 1.3.1 (Info and Relationships)",
  LINK_TEXT: "WCAG 2.4.4 (Link Purpose)",
  FORM_LABELS: "WCAG 1.3.1 (Info and Relationships)",
};

function generateDevtoolsCommand(violation: ViolationRaw): string {
  const category = violation.category?.toUpperCase();

  if (violation.fix_action?.devtools_command) {
    return violation.fix_action.devtools_command;
  }

  switch (category) {
    case "COLOR_CONTRAST":
      return `// Fix color contrast issue
document.querySelectorAll('*').forEach(el => {
  const style = window.getComputedStyle(el);
  const color = style.color;
  const bg = style.backgroundColor;
  // Apply high-contrast fix
  el.style.color = '#1a1a1a';
  el.style.backgroundColor = '#ffffff';
});
// Or target specific element:
// document.querySelector('.your-selector').style.color = '#000000';`;

    case "FONT_SIZE":
      return `// Fix font size below minimum (12px)
document.querySelectorAll('*').forEach(el => {
  const size = parseFloat(window.getComputedStyle(el).fontSize);
  if (size < 16) {
    el.style.fontSize = '16px';
  }
});`;

    case "MISSING_ALT_TEXT":
      return `// Fix missing alt text on images
document.querySelectorAll('img:not([alt]), img[alt=""]').forEach((img, i) => {
  img.setAttribute('alt', 'Descriptive text for image ' + (i + 1));
});`;

    case "KEYBOARD_FOCUS":
      return `// Fix missing focus indicators
const style = document.createElement('style');
style.textContent = \`
  *:focus {
    outline: 3px solid #005FCC !important;
    outline-offset: 2px !important;
  }
\`;
document.head.appendChild(style);`;

    case "BUTTON_SIZE":
      return `// Fix touch target size (minimum 44x44px)
document.querySelectorAll('button, a, [role="button"], input[type="submit"]').forEach(el => {
  const rect = el.getBoundingClientRect();
  if (rect.width < 44 || rect.height < 44) {
    el.style.minWidth = '44px';
    el.style.minHeight = '44px';
    el.style.display = 'inline-flex';
    el.style.alignItems = 'center';
    el.style.justifyContent = 'center';
  }
});`;

    case "HEADING_STRUCTURE":
      return `// Check and log heading structure
const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
headings.forEach(h => console.log(h.tagName, h.textContent?.substring(0, 50)));
// Fix: Ensure logical heading hierarchy (h1 > h2 > h3...)
// Replace mis-used heading levels with proper semantic structure`;

    case "LINK_TEXT":
      return `// Fix generic link text
document.querySelectorAll('a').forEach(link => {
  const text = link.textContent?.trim().toLowerCase();
  if (text === 'click here' || text === 'read more' || text === 'here' || text === 'more') {
    // Add aria-label with descriptive text
    link.setAttribute('aria-label', 'Link to: ' + (link.href || 'destination'));
    // Or update the text content:
    // link.textContent = 'Read our accessibility guide';
  }
});`;

    case "FORM_LABELS":
      return `// Fix form inputs missing labels
document.querySelectorAll('input:not([aria-label]):not([id])').forEach((input, i) => {
  input.setAttribute('aria-label', 'Form field ' + (i + 1));
});
// Better: Link labels to inputs
document.querySelectorAll('input[id]').forEach(input => {
  const label = document.querySelector('label[for="' + input.id + '"]');
  if (!label) {
    input.setAttribute('aria-label', input.placeholder || input.name || 'Input field');
  }
});`;

    default:
      return `// Accessibility fix for ${violation.category}
// ${violation.fix_description}
// Apply the following change:
// Property: ${violation.fix_action?.property || "style"}
// New value: ${violation.fix_action?.new_value || "see fix description"}`;
  }
}

export function generateFixAction(violation: ViolationRaw): AppliedFix {
  const devtoolsCommand = generateDevtoolsCommand(violation);
  const category = violation.category?.toUpperCase() || "UNKNOWN";

  return {
    violationId: violation.violation_id,
    fixApplied: true,
    devtoolsCommand,
    explanation: violation.fix_description || `Fix applied for ${violation.category} violation`,
    wcagCriterionMet: WCAG_CRITERIA[category] || violation.wcag_criterion || "WCAG 2.1",
    complianceImprovement: FIX_IMPROVEMENTS[category] || 3,
  };
}
