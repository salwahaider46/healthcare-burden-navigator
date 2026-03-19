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
| GET | `/api/v1/providers/search` | Search providers by name, specialty, city, state, zip, insurance |
| GET | `/api/v1/providers/{id}` | Get a single provider by ID |
