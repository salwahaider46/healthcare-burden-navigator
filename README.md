# Healthcare Burden Navigator

Group 089 – CS-6440 Introduction to Health Informatics

## Project Structure

```
backend/        # FastAPI backend (Salwa)
frontend/       # React chatbot UI (Salwa)
```

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # update values as needed
uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

## Frontend Setup (Sprint 5)

```bash
cd frontend
npm install
npm run dev
```

Chat UI available at: http://localhost:5173

The chatbot accepts natural language input (e.g. *"Find a cardiologist near 30318 that takes Medicaid and offers telehealth"*), extracts filters via Gemini, and returns ranked provider recommendations.

> **Requires:** `GEMINI_API_KEY` set in `backend/.env`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/providers/recommendations` | Ranked provider results filtered by specialty, insurance, telehealth, distance, and optional FHIR patient context |
| GET | `/api/v1/providers/search` | Search providers by name, specialty, city, state, zip, insurance |
| GET | `/api/v1/providers/{id}` | Get a single provider by ID |
| GET | `/api/v1/providers/{id}/details` | Get provider merged with FHIR Practitioner data |
| GET | `/api/v1/fhir/practitioners` | Search FHIR Practitioner resources |
| GET | `/api/v1/fhir/practitioners/{fhir_id}` | Get a single FHIR Practitioner |
| GET | `/api/v1/fhir/conditions` | Search FHIR Condition resources by patient |
| GET | `/api/v1/fhir/encounters` | Search FHIR Encounter resources by patient |
| GET | `/api/v1/fhir/coverage` | Search FHIR Coverage resources by patient |
| POST | `/api/v1/chat` | Natural language chatbot — extracts filters via Gemini and returns ranked providers |

## Sprint 4 Demo Checklist

Use this checklist for the status check-in demo (under 5 minutes).

1) Confirm API is up:

```bash
curl -s http://localhost:8000/
```

Expected keys: `status`, `message`

2) Verify raw FHIR Condition search:

```bash
curl -s "http://localhost:8000/api/v1/fhir/conditions?subject=<PATIENT_ID>"
```

Expected bundle fields: `resourceType`, optional `entry`

3) Verify raw FHIR Coverage search:

```bash
curl -s "http://localhost:8000/api/v1/fhir/coverage?beneficiary=<PATIENT_ID>"
```

Expected bundle fields: `resourceType`, optional `entry`

4) Verify recommendations endpoint uses patient context:

```bash
curl -s "http://localhost:8000/api/v1/providers/recommendations?patient_id=<PATIENT_ID>&limit=5"
```

Expected provider fields (per result): `id`, `name`, `specialty`, `insurance_accepted`, `telehealth`, `rank_score`, `distance_miles`

Implementation note for Sprint 4: patient `Condition` and `Coverage` are normalized in `fhir_client.py` before ranking is called.

## Database Changes (Sprint 4)

The `providers` table has three new columns added in Sprint 4:

```
telehealth   BOOLEAN   -- whether provider offers telehealth
latitude     FLOAT     -- provider location latitude
longitude    FLOAT     -- provider location longitude
```

If you already have a local database, drop and recreate it (or run an ALTER TABLE) to pick up these columns:

```bash
# easiest: drop and recreate
psql -U postgres -c "DROP DATABASE healthcare_nav;"
psql -U postgres -c "CREATE DATABASE healthcare_nav;"
uvicorn main:app --reload  # SQLAlchemy will recreate the schema on startup
```
