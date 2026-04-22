# app/main.py
import os
import shutil

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# Pipeline: ingest -> analyze -> assemble report
from app.services.ingestion import process_contract
from app.services.clause_analyzer import analyze as analyze_clauses
from app.services.report_builder import build as build_report

load_dotenv()

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
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        extraction = await process_contract(temp_path)
        findings = await analyze_clauses(extraction, db)
        report = build_report(extraction, findings)
        return report
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
