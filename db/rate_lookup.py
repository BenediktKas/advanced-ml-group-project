"""Rate benchmark lookup (Layer 1 — Relational Facts).

Returns hourly-rate percentiles (p25 / median / p75) for a given
skill_category + experience level, preferring region-specific data and
falling back to nationwide. Returns None if no benchmark exists.
"""
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_EXPERIENCE_LEVELS = ("junior", "mid", "senior")

# Canonical English skill categories actually present in `rate_benchmarks`
# (see db/seed_rates.sql). Anything else the LLM emits should be funneled
# into one of these via _normalize_skill_category, otherwise the lookup
# silently misses and clause_analyzer cannot raise a "rate below p25"
# finding.
CANONICAL_SKILL_CATEGORIES = (
    "Consulting & Management",
    "SAP Consulting",
    "IT Infrastructure",
    "Engineering",
    "Software Development",
    "Marketing & Communications",
    "Design & Content",
    "Other",
)

# Order matters: more specific matches must come first. SAP and
# IT-Infrastructure keywords are checked BEFORE the generic
# "Software Development" / "Engineering" buckets so that, e.g.,
# "SAP ABAP developer" lands in SAP Consulting rather than
# Software Development, and "DevOps engineer" lands in
# IT Infrastructure rather than Engineering. Non-software
# Engineering keywords are checked BEFORE Software Development
# so "Mechanical engineer" doesn't get caught by the generic
# "engineer" keyword.
_SKILL_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("SAP Consulting", (
        "sap", "abap", "s/4hana", "s4hana", "fiori", "hana",
    )),
    ("IT Infrastructure", (
        "devops", "sre", "site reliability", "infrastructure", "infrastruktur",
        "cloud", "aws", "azure", "gcp", "kubernetes", "k8s", "docker",
        "network", "netzwerk", "system administrator", "sysadmin",
        "security", "sicherheit", "cybersecurity", "it-security",
        "datenbank", "database admin", "dba", "platform",
    )),
    ("Engineering", (  # non-software engineering — checked BEFORE Software Development
        "ingenieur", "mechanical", "maschinenbau", "elektrotechnik",
        "electrical engineer", "civil", "bauingenieur", "chemical",
        "verfahrenstechnik", "automotive", "automobil", "luft- und raumfahrt",
        "aerospace", "process engineer",
    )),
    ("Software Development", (
        "software", "developer", "entwickl", "programmier", "engineer",
        "frontend", "backend", "full stack", "fullstack", "full-stack",
        "java", "python", "javascript", "typescript", "react", "angular",
        "vue", "node", "rust", "golang", "go developer", ".net", "c#", "c++",
        "mobile", "ios", "android", "data engineer", "ml engineer",
        "machine learning", "data scientist", "ki-",
    )),
    ("Consulting & Management", (
        "consult", "berat", "manage", "projekt", "project manager", "pmo",
        "scrum", "agile coach", "product owner", "business analyst",
        "strategy", "strategie", "transformation", "change",
    )),
    ("Design & Content", (
        "design", "ux", "ui", "grafik", "graphic", "content", "redakteur",
        "redaktion", "copywriter", "texter", "video", "fotograf",
        "photograph", "illustrator",
    )),
    ("Marketing & Communications", (
        "marketing", "kommunikation", "communications", "pr ", "public relation",
        "social media", "seo", "sea", "performance", "brand", "campaign",
        "kampagne", "werbung", "advertising",
    )),
]


def _normalize_skill_category(raw: Optional[str]) -> str:
    """Map a free-text skill label onto a canonical `skill_category`.

    The ingestion LLM (gpt-4o-mini) returns whatever phrase best fits
    the contract — German or English, narrow or broad. The seeded
    `rate_benchmarks` table only stores 8 English buckets, so we need
    a deterministic bridge between the two. Substring matching is
    case-insensitive and order-sensitive (see _SKILL_KEYWORDS).

    Returns "Other" as a safe fallback so the SQL lookup always has
    something to bind to. "Other" is itself a valid seeded bucket and
    its rates approximate the cross-category median.
    """
    if not raw:
        return "Other"

    # Direct hit (LLM already returned a canonical label)
    for canonical in CANONICAL_SKILL_CATEGORIES:
        if raw.strip().lower() == canonical.lower():
            return canonical

    r = raw.lower()
    for canonical, keywords in _SKILL_KEYWORDS:
        if any(kw in r for kw in keywords):
            return canonical
    return "Other"


class RateBenchmark(BaseModel):
    skill_category: str
    region: Optional[str]
    experience: str
    p25: float
    median: float
    p75: float
    source: str
    source_year: int


def _normalize_experience(raw: str) -> Optional[str]:
    """Map free-text experience labels onto the DB's CHECK-constrained set."""
    if not raw:
        return None
    r = raw.strip().lower()
    if r in _EXPERIENCE_LEVELS:
        return r
    if r in ("entry", "entry-level", "entry level", "beginner"):
        return "junior"
    if r in ("intermediate", "middle", "mid-level", "mid level"):
        return "mid"
    if r in ("expert", "lead", "principal", "staff"):
        return "senior"
    return None


async def lookup(
    skill_category: str,
    experience: str,
    session: AsyncSession,
    region: Optional[str] = None,
) -> Optional[RateBenchmark]:
    """Lookup a rate benchmark. Region-specific first, then national."""
    exp = _normalize_experience(experience)
    if exp is None:
        return None

    # Bridge free-text LLM output → canonical seeded bucket
    canonical_skill = _normalize_skill_category(skill_category)
    params = {"skill": canonical_skill, "exp": exp}

    if region:
        q = text(
            """
            SELECT skill_category, region, experience,
                   p25_eur_per_h  AS p25,
                   median_eur_per_h AS median,
                   p75_eur_per_h  AS p75,
                   source, source_year
            FROM rate_benchmarks
            WHERE skill_category = :skill
              AND experience     = :exp
              AND region         = :region
            ORDER BY source_year DESC
            LIMIT 1
            """
        )
        row = (await session.execute(q, {**params, "region": region})).mappings().first()
        if row:
            return RateBenchmark(**dict(row))

    q = text(
        """
        SELECT skill_category, region, experience,
               p25_eur_per_h  AS p25,
               median_eur_per_h AS median,
               p75_eur_per_h  AS p75,
               source, source_year
        FROM rate_benchmarks
        WHERE skill_category = :skill
          AND experience     = :exp
          AND region IS NULL
        ORDER BY source_year DESC
        LIMIT 1
        """
    )
    row = (await session.execute(q, params)).mappings().first()
    if row:
        return RateBenchmark(**dict(row))
    return None
