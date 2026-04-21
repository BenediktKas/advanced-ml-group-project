import pdfplumber
import os
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import List, Optional

# Define schema for extraction based on Technical Architecture Step 1
class ContractExtraction(BaseModel):
    skill_category: str
    region: Optional[str]
    experience_level: str
    hourly_rate_eur: float
    payment_terms_days: int
    clauses: List[str]

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def process_contract(file_path: str) -> ContractExtraction:
    # 1. Raw Text Extraction
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    
    # 2. Structured Extraction (using GPT-4o-mini for cost-efficiency)
    # per architecture recommendation [cite: 262]
    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract German freelancer contract terms into JSON."},
            {"role": "user", "content": text}
        ],
        response_format=ContractExtraction,
    )
    return response.choices[0].message.parsed