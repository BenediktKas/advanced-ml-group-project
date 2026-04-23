# German Freelancer Contract Analyzer


## Setup Instructions

These instructions cover setting up the environment, PostgreSQL database, and Python services natively on your local machine (macOS/Linux).

### 1. Prerequisites & Database
The pipeline uses a local PostgreSQL database with the **pgvector** extension.

1. **Install PostgreSQL and pgvector via Homebrew** (macOS):
   ```bash
   brew install postgresql pgvector
   brew services start postgresql
   ```

2. **Provision the Database**:
   Create the database and the expected user in `psql`:
   ```sql
   CREATE USER postgres WITH PASSWORD 'password' SUPERUSER;
   CREATE DATABASE freelancer_analyzer OWNER postgres;
   ```
   *(Ensure these credentials match the `DATABASE_URL` in your `.env` file).*

3. **Load the Schema**:
   From the repository root, inject the tables and initial static data:
   ```bash
   psql -U postgres -d freelancer_analyzer -f db/init.sql
   ```

### 2. Environment & Dependencies

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python Packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   - Copy `.env.example` to a new `.env` file.
   - Insert your real `OPENAI_API_KEY` (must support `text-embedding-3-small` and `gpt-4o-mini`).

### 3. Seed the Playbook Vectors
The application compares contract clauses against a statutory embedded playbook relying on vector similarity. You must generate embeddings for the database:

```bash
python scripts/seed_vectors.py
```
*Note: This will cost a few cents in OpenAI API credits as it generates vector embeddings for the rules.*

---

## Running the Application

The analyzer consists of a FastAPI backend and a Streamlit interactive frontend. They must be run simultaneously in **two separate terminal windows**.

### Window 1: Start the Backend server
The backend handles the PDF data extraction, LLM structuring, and vector comparison computations.
```bash
# Make sure your environment is activated
source .venv/bin/activate
uvicorn app.main:app --reload
```
*This server will run at `http://localhost:8000`.*

### Window 2: Start the Frontend UI
The Streamlit application presents the parsed data, contract risks, warnings, and suggested redlines interactively.
```bash
# Make sure your environment is activated
source .venv/bin/activate
streamlit run UX/UX.py
```
*This will open the user interface at `http://localhost:8501`.*

## Testing with Sample Data
A mock contract exists under `tests/samples/sample.pdf` that triggers simulated risk warnings for hourly rates, IP, Scheinselbstständigkeit, and payment terms. Simply drop it into the running Streamlit upload box to see the pipeline end to end!
