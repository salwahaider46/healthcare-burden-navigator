# Healthcare Burden Navigator

Group 089 – CS-6440 Introduction to Health Informatics

## Project Structure

```
backend/        # FastAPI backend (Salwa)
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
