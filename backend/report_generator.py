import io
import html
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

WHITE    = colors.white
OFFWHITE = colors.HexColor("#F8F9FA")
BORDER   = colors.HexColor("#DEE2E6")
PRIMARY  = colors.HexColor("#0D6EFD")  # Bootstrap Blue
SUCCESS  = colors.HexColor("#198754")
DANGER   = colors.HexColor("#DC3545")
WARNING  = colors.HexColor("#FFC107")
TEXT     = colors.HexColor("#212529")
MUTED    = colors.HexColor("#6C757D")


def _e(text: str) -> str:
    """Escape HTML special characters so ReportLab XML parser doesn't choke."""
    return html.escape(str(text or ""), quote=False)


def _severity_color(s: str) -> colors.HexColor:
    return {
        "critical": DANGER,
        "serious":  DANGER,
        "moderate": WARNING,
        "minor":    SUCCESS,
    }.get((s or "").lower(), MUTED)


def generate_pdf_report(scan_data: Dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm,  bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        textColor=PRIMARY,
        fontSize=26,
        fontName="Helvetica-Bold",
        spaceAfter=12,
        alignment=TA_LEFT
    )
    
    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        textColor=TEXT,
        fontSize=18,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=10,
        borderPadding=(0, 0, 2, 0),
        borderWidth=0,
        borderColor=PRIMARY
    )
    
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        textColor=PRIMARY,
        fontSize=14,
        fontName="Helvetica-Bold",
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        textColor=TEXT,
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    label_style = ParagraphStyle(
        "Label",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=10
    )

    code_style = ParagraphStyle(
        "Code",
        parent=styles["Code"],
        fontSize=8,
        textColor=DANGER,
        backColor=OFFWHITE,
        borderPadding=5,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=4,
        spaceAfter=4
    )

    muted_style = ParagraphStyle(
        "Muted",
        parent=body_style,
        textColor=MUTED,
        fontSize=9
    )

    # Data extraction
    target_url = scan_data.get("url", "Unknown URL")
    quality_score = scan_data.get("quality_score", scan_data.get("qualityScore", 0))
    bugs = scan_data.get("all_bugs", scan_data.get("allBugs", [])) or []
    created_at = scan_data.get("created_at", scan_data.get("createdAt", datetime.now().isoformat()))
    perf = scan_data.get("performance_metrics", scan_data.get("performanceMetrics", {})) or {}
    
    story = []

    # --- Header Section ---
    story.append(Paragraph("QA Testing Analysis Report", title_style))
    story.append(Paragraph(f"Target: <font color='#0D6EFD'>{_e(target_url)}</font>", body_style))
    story.append(Paragraph(f"Date: {created_at[:16].replace('T', ' ')}", muted_style))
    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=8))

    # --- Executive Summary ---
    story.append(Paragraph("Executive Summary", h1_style))
    
    score_color = "#198754" if quality_score >= 80 else ("#FFC107" if quality_score >= 60 else "#DC3545")
    
    summary_data = [
        [Paragraph("Health Score", label_style), Paragraph("Total Issues", label_style), Paragraph("Critical", label_style)],
        [
            Paragraph(f'<font size="28" color="{score_color}"><b>{quality_score}%</b></font>', body_style),
            Paragraph(f'<font size="24">{len(bugs)}</font>', body_style),
            Paragraph(f'<font size="24" color="#DC3545">{sum(1 for b in bugs if (b.get("severity") or "").lower() == "critical")}</font>', body_style)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[60 * mm, 60 * mm, 60 * mm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), OFFWHITE),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8 * mm))

    # --- Performance Metric ---
    if perf:
        story.append(Paragraph("Performance & Infrastructure", h2_style))
        perf_data = [["Metric", "Result"]]
        labels = {
            "initial_load_ms": "Initial Page Load",
            "pages_scanned": "Pages Analyzed",
            "total_requests": "Network Requests",
            "error_count": "Network Failures"
        }
        for k, v in labels.items():
            if k in perf:
                val = f"{perf[k]}ms" if "ms" in k else str(perf[k])
                perf_data.append([v, val])
        
        pt = Table(perf_data, colWidths=[100 * mm, 80 * mm])
        pt.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, OFFWHITE]),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(pt)
        story.append(Spacer(1, 10 * mm))

    # --- Issue Details ---
    if bugs:
        story.append(Paragraph("Detailed Findings", h1_style))
        
        for i, bug in enumerate(bugs):
            sev = (bug.get("severity") or "moderate").lower()
            scolor = _severity_color(sev)
            
            # Issue Header
            issue_title = [
                [
                    Paragraph(f"<b>#{i+1} {bug.get('category', 'Issue').upper()}</b>", ParagraphStyle("T", parent=body_style, textColor=WHITE)),
                    Paragraph(sev.upper(), ParagraphStyle("S", parent=body_style, alignment=TA_CENTER, textColor=WHITE, fontName="Helvetica-Bold"))
                ]
            ]
            it = Table(issue_title, colWidths=[140 * mm, 40 * mm])
            it.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), scolor),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(KeepTogether([
                it,
                Paragraph(f"<b>Location:</b> {bug.get('label', 'Multiple Pages')}", muted_style),
                Paragraph(bug.get('description', 'No description available'), body_style),
            ]))
            
            if bug.get('element'):
                story.append(Paragraph(f"<b>Target:</b> <font face='Courier' size='8'>{_e(bug['element'])}</font>", muted_style))
                
            if bug.get('css_fix') or bug.get('cssFix'):
                story.append(Paragraph("<b>Recommended Fix:</b>", label_style))
                story.append(Paragraph(_e(bug.get('css_fix') or bug.get('cssFix')), code_style))
            
            story.append(Spacer(1, 6 * mm))

    # --- Footer ---
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(15 * mm, 10 * mm, "QA Testing Tool - Professional Quality Assurance Report")
        canvas.drawRightString(A4[0] - 15 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
