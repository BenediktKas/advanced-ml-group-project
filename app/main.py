# app/main.py
import os
import shutil
import tempfile

from dotenv import load_dotenv

# Load .env BEFORE importing app.services / db modules. Several of them
# instantiate AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) at import
# time, so the key must already be in the environment by then.
load_dotenv()

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Pipeline: ingest -> analyze -> assemble report
from app.services.ingestion import process_contract
from app.services.clause_analyzer import analyze as analyze_clauses
from app.services.report_builder import build as build_report

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="German Freelancer Contract Analyzer")
engine = create_async_engine(DATABASE_URL, echo=True)


async def get_db():
    async with AsyncSession(engine) as session:
        yield session


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Verify API is up and the database connection is functional."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/analyze")
async def analyze_contract(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Full analysis pipeline: ingest -> analyze -> assemble report.

    1. Ingest  - PDF -> structured ContractExtraction (GPT-4o-mini).
    2. Analyze - per-clause risk analysis against playbook, statutes, rates.
    3. Report  - summary counts, findings list, negotiation brief.
    """
    # Use a NamedTemporaryFile so concurrent uploads never collide on the
    # same path and a malicious `file.filename` (e.g. "../../etc/passwd")
    # can't escape the working directory.
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        try:
            extraction = await process_contract(temp_path)
        except ValueError as e:
            # Scanned / unreadable PDFs raise ValueError in ingestion.
            # Return a 400 so the client gets a clean error instead of a 500.
            raise HTTPException(status_code=400, detail=str(e))

        findings = await analyze_clauses(extraction, db)
        report = build_report(extraction, findings)
        return report
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
