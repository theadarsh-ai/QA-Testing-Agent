from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class FixAction(CamelModel):
    type: str
    property: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    devtools_command: str


class Violation(CamelModel):
    violation_id: str
    category: str
    severity: str
    element_description: str
    wcag_criterion: str
    current_value: Optional[str] = None
    required_value: Optional[str] = None
    fix_description: str
    fix_action: Optional[FixAction] = None


class ScanRequest(CamelModel):
    user_id: str
    url: str
    screenshot_base64: str


class AppliedFix(CamelModel):
    violation_id: str
    fix_applied: bool
    devtools_command: str
    explanation: str
    wcag_criterion_met: str
    compliance_improvement: int


class ScanResult(CamelModel):
    scan_id: str
    violations_found: List[Violation]
    fixes_applied: List[AppliedFix]
    compliance_score_before: int
    compliance_score_after: int
    total_violations: int
    critical_count: int
    serious_count: int
    moderate_count: int
    page_summary: str


class ApplyFixRequest(CamelModel):
    scan_id: str
    violation_id: str


class FixDetail(CamelModel):
    action_type: str
    target_element: str
    fix_code: str
    explanation: str


class ScanSummary(CamelModel):
    scan_id: str
    url: str
    created_at: str
    compliance_score_before: int
    compliance_score_after: int
    total_violations: int
    critical_count: int
    serious_count: int
    moderate_count: int
    page_summary: str


class ScanHistoryResponse(CamelModel):
    scans: List[ScanSummary]
