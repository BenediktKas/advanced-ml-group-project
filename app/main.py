# app/main.py
import os
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv

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
        # Ping the database
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}