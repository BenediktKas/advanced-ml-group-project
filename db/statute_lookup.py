"""Statute reference lookup (Layer 1 — Relational Facts).

Returns the German statutory references (BGB, SGB IV, UrhG, etc.) most
relevant to a given clause_type. Used by clause_analyzer to ground LLM
reasoning in authoritative legal text.
"""
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class StatuteRef(BaseModel):
    paragraph: str
    text_excerpt: str
    official_url: Optional[str] = None


async def lookup(clause_type: str, session: AsyncSession) -> List[StatuteRef]:
    """All statute references matching `clause_type` (e.g. 'late_payment_interest')."""
    if not clause_type:
        return []

    q = text(
        """
        SELECT paragraph, text_excerpt, official_url
        FROM statute_references
        WHERE clause_type = :ct
        """
    )
    rows = (await session.execute(q, {"ct": clause_type})).mappings().all()
    return [StatuteRef(**dict(r)) for r in rows]
