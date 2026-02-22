
from datetime import datetime
from pathlib import Path

# === Utility functions to export BRR text to PDF ===

def format_brr(fields: dict, confidence: float, corrections: dict) -> str:
    """Format extracted fields into a readable BRR string."""
    lines = [
        "=" * 60,
        "BUILD READINESS REVIEW - AUTOMATED OUTPUT",
        "=" * 60,
        f"Generated:        {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Confidence Score: {confidence:.0f}%",
        f"Human Corrected:  {'Yes' if corrections else 'No'}",
        "",
        "── GO/NO-GO STATUS ──────────────────────────────────",
        f"  {fields.get('go_no_go_status', 'UNKNOWN')}",
        "",
        "── APPROVALS ────────────────────────────────────────",
    ]

    for a in fields.get("approvals", []) or [{"name": "None found", "role": "", "conditions": None}]:
        name = a.get("name", "Unknown")
        role = a.get("role", "")
        conditions = a.get("conditions") or "None"
        lines.append(f"  • {name} ({role}) > Conditions: {conditions}")

    lines += ["", "── RISKS ────────────────────────────────────────────"]

    for r in fields.get("risks", []) or [{"description": "None found", "severity": "UNKNOWN", "mitigation": None}]:
        lines.append(f"  • [{r.get('severity', 'UNKNOWN')}] {r.get('description', '')}")
        lines.append(f"    Mitigation: {r.get('mitigation') or 'None'}")

    lines += [
        "",
        "── TEST SUMMARY ─────────────────────────────────────",
        f"  {fields.get('test_summary') or 'No test summary provided.'}",
        "",
        "=" * 60,
    ]

    return "\n".join(lines)


def export_pdf(brr_text: str, output_path: Path) -> None:
    """Write BRR text to a PDF file using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.HexColor("#16213e"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
    )

    story = []

    for line in brr_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("="):
            story.append(Spacer(1, 4))
        elif "BUILD READINESS REVIEW" in stripped:
            story.append(Paragraph(stripped, title_style))
        elif stripped.startswith("──"):
            story.append(Paragraph(stripped.replace("─", "").strip(), section_style))
        else:
            story.append(Paragraph(stripped, body_style))

    doc.build(story)