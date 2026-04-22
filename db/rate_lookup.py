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

    params = {"skill": skill_category, "exp": exp}

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
