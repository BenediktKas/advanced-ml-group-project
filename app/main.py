# app/main.py
import os
import shutil
from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv

# Import the service you are about to create
from app.services.ingestion import process_contract

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(title="German Freelancer Contract Analyzer")
engine = create_async_engine(DATABASE_URL, echo=True)

async def get_db():
    async with AsyncSession(engine) as session:
        yield session

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Verifies that the API is up and the database connection is functional.
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/analyze")
async def analyze_contract(file: UploadFile = File(...)):
    """
    Step 1 & 2 of the Analysis Pipeline: Ingestion and Structured Extraction.
    """
    # 1. Save temporary file to disk for processing
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # 2. Run the Ingestion Service logic
        # This calls the LLM to extract terms into structured JSON
        data = await process_contract(temp_path)
        return {"extracted_data": data}
    finally:
        # 3. Cleanup: Always remove the temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)