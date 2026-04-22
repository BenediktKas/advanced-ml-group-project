"""Populate the playbook.embedding column for rows where it is NULL.

Each playbook row is composed into a semantic text blob (clause type,
pattern description, example risky wording, recommended redline, legal
reasoning), embedded with OpenAI text-embedding-3-small (1536-dim),
and the resulting vector is written back to the `embedding` column.

Usage:
    python scripts/seed_vectors.py            # only rows where embedding IS NULL
    python scripts/seed_vectors.py --force    # re-embed every row

Requires DATABASE_URL and OPENAI_API_KEY in .env (loaded automatically).
Pgvector extension must already be installed (see db/init.sql).
"""
import argparse
import asyncio
import os
import sys
from typing import List

from dotenv import load_dotenv
from openai import AsyncOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536


def _compose_text(row) -> str:
    """Build the text blob used to compute the embedding for a playbook entry.

    Concatenates every semantically useful field so the embedding captures
    both the English meta-description and the German recommended redline —
    text-embedding-3-small handles the cross-lingual case reasonably.
    """
    parts = [f"Clause type: {row['clause_type']}",
             f"Pattern: {row['pattern_description']}"]
    if row.get("example_risky_wording"):
        parts.append(f"Example risky wording: {row['example_risky_wording']}")
    if row.get("recommended_redline"):
        parts.append(f"Recommended redline: {row['recommended_redline']}")
    if row.get("legal_reasoning"):
        parts.append(f"Legal reasoning: {row['legal_reasoning']}")
    return "\n".join(parts)


def _to_pgvector_literal(vec: List[float]) -> str:
    """pgvector accepts a literal like '[0.1,0.2,...]' when CAST AS vector."""
    return "[" + ",".join(f"{v:.8f}" for v in vec) + "]"


async def main(force: bool = False) -> None:
    if not DATABASE_URL:
        sys.exit("DATABASE_URL not set (check .env)")
    if not OPENAI_API_KEY:
        sys.exit("OPENAI_API_KEY not set (check .env)")

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    engine = create_async_engine(DATABASE_URL, echo=False)

    where_clause = "" if force else "WHERE embedding IS NULL"
    select_sql = text(
        f"""
        SELECT id, clause_type, pattern_description, example_risky_wording,
               recommended_redline, legal_reasoning
        FROM playbook
        {where_clause}
        ORDER BY id
        """
    )

    async with AsyncSession(engine) as session:
        rows = (await session.execute(select_sql)).mappings().all()
        if not rows:
            print("Nothing to embed — all playbook entries already have vectors.")
            await engine.dispose()
            return

        total = len(rows)
        print(f"Embedding {total} playbook entr{'y' if total == 1 else 'ies'} "
              f"with {EMBED_MODEL}...")

        succeeded = 0
        failed = 0
        for row in rows:
            blob = _compose_text(row)
            try:
                resp = await client.embeddings.create(model=EMBED_MODEL, input=blob)
                vec = resp.data[0].embedding
                if len(vec) != EMBED_DIM:
                    print(f"  [{row['id']}] unexpected embedding dim {len(vec)} "
                          f"(expected {EMBED_DIM}) — skipping")
                    failed += 1
                    continue

                await session.execute(
                    text("UPDATE playbook SET embedding = CAST(:vec AS vector) "
                         "WHERE id = :id"),
                    {"vec": _to_pgvector_literal(vec), "id": row["id"]},
                )
                print(f"  [{row['id']}] embedded ({len(blob)} chars)")
                succeeded += 1
            except Exception as e:
                print(f"  [{row['id']}] FAILED: {type(e).__name__}: {e}")
                failed += 1

        await session.commit()
        print(f"Done. {succeeded} succeeded, {failed} failed.")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed playbook.embedding column")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed every row, not just those where embedding IS NULL.",
    )
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
