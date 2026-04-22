"""Vector search over the playbook (Layer 2 — Curated Risky-Clause Patterns).

Given a clause snippet from an ingested contract, embeds it with OpenAI
text-embedding-3-small (1536-dim, matching the playbook.embedding column)
and runs a pgvector cosine-distance query against the playbook table.

Returns the top-k candidates above a similarity floor. If no playbook
entries have embeddings yet, returns an empty list — callers should
handle gracefully.
"""
import os
from typing import List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class PlaybookMatch(BaseModel):
    id: str
    clause_type: str
    risk_level: str
    pattern_description: str
    example_risky_wording: Optional[str] = None
    legal_reasoning: str
    recommended_redline: Optional[str] = None
    statute_ref: Optional[str] = None
    similarity: float  # 1.0 = identical, 0.0 = orthogonal


async def embed(text_in: str) -> List[float]:
    """Return a single embedding vector for `text_in`."""
    resp = await _client.embeddings.create(model=EMBED_MODEL, input=text_in)
    return resp.data[0].embedding


def _to_pgvector_literal(vec: List[float]) -> str:
    """pgvector accepts string literals like '[0.1,0.2,...]' when cast to vector."""
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"


async def lookup(
    clause_text: str,
    session: AsyncSession,
    top_k: int = 3,
    min_similarity: float = 0.25,
) -> List[PlaybookMatch]:
    """Top-k playbook entries most similar to `clause_text`.

    Uses pgvector's `<=>` (cosine distance) operator; similarity is
    1 - cosine_distance, so higher is better. Rows whose embedding is NULL
    are skipped (seed_vectors.py populates embeddings after insert).
    """
    if not clause_text or not clause_text.strip():
        return []

    vec_literal = _to_pgvector_literal(await embed(clause_text))

    query = text(
        """
        SELECT id, clause_type, risk_level, pattern_description,
               example_risky_wording, legal_reasoning, recommended_redline,
               statute_ref,
               1 - (embedding <=> CAST(:qvec AS vector)) AS similarity
        FROM playbook
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :k
        """
    )
    result = await session.execute(query, {"qvec": vec_literal, "k": top_k})
    rows = result.mappings().all()
    return [PlaybookMatch(**dict(r)) for r in rows if r["similarity"] >= min_similarity]
