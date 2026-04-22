"""Assemble the final analysis report for the UI.

Takes a list of Findings plus the ContractExtraction and returns the
structured JSON that the Streamlit UI expects: summary counts, the
findings themselves, and a negotiation brief.
"""
from datetime import date
from typing import Dict, List

from pydantic import BaseModel

from app.services.clause_analyzer import Finding
from app.services.ingestion import ContractExtraction


class AnalysisReport(BaseModel):
    profile: str
    date: str
    summary: Dict[str, int]
    findings: List[Finding]
    brief: str


def _build_brief(profile: str, findings: List[Finding]) -> str:
    priorities = [f for f in findings if f.risk in ("high", "medium")]
    acceptable = [f for f in findings if f.risk == "low"]

    lines: List[str] = [f"Profile: {profile}", f"Date: {date.today().isoformat()}", ""]

    if priorities:
        lines.append("Priority actions:")
        for i, f in enumerate(priorities, start=1):
            severity = "high" if f.risk == "high" else "medium"
            entry = f"  {i}. {f.title} ({severity} priority). {f.body}"
            if f.redline:
                entry += f"\n     Suggested redline: {f.redline}"
            if f.statute:
                entry += f"\n     Statute: {f.statute}"
            lines.append(entry)
    else:
        lines.append("Priority actions: none identified.")

    if acceptable:
        lines.append("")
        lines.append("Within standard scope:")
        for f in acceptable:
            lines.append(f"  - {f.title}")

    lines.append("")
    lines.append("For informational purposes only. This analysis does not constitute legal advice.")
    return "\n".join(lines)


def build(extraction: ContractExtraction, findings: List[Finding]) -> AnalysisReport:
    """Assemble the UI-ready report."""
    summary = {
        "high": sum(1 for f in findings if f.risk == "high"),
        "medium": sum(1 for f in findings if f.risk == "medium"),
        "low": sum(1 for f in findings if f.risk == "low"),
        "total": len(findings),
    }

    profile = (
        f"{extraction.experience_level.title()} {extraction.skill_category}"
        f" · {extraction.region or 'Germany'}"
    )

    return AnalysisReport(
        profile=profile,
        date=date.today().isoformat(),
        summary=summary,
        findings=findings,
        brief=_build_brief(profile, findings),
    )
