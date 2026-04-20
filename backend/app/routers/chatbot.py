import json
import os
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import fhir_client, models, schemas
from app.database import get_db
from app.services.filtering import apply_filters, compute_distance_miles
from app.services.ranking import rank_providers

router = APIRouter(prefix="/chat", tags=["chatbot"])

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-flash-latest:generateContent"
)


def _call_gemini(prompt: str) -> str:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    response = httpx.post(
        GEMINI_URL,
        headers={"X-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

EXTRACT_PROMPT = """\
You are a healthcare search assistant. Extract structured search filters from
the user's natural language message and return ONLY a JSON object with these
optional fields (omit fields not mentioned):

{{
  "specialty":          string,
  "insurance":          string,
  "telehealth":         boolean,
  "zip_code":           string,
  "max_distance_miles": number,
  "language":           string,
  "reply":              string
}}

User message: {message}
"""


class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    patient_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    filters: dict
    providers: list[schemas.RankedProviderOut]


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Accept a natural language message, extract provider search filters using
    Gemini, run the ranked recommendations query, and return results with a
    conversational reply.
    """
    # 1. Extract filters from the user message via Gemini
    prompt = EXTRACT_PROMPT.format(message=request.message)
    try:
        raw = _call_gemini(prompt).strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        filters = json.loads(raw.strip())
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini error: {type(e).__name__}: {str(e)} | raw={locals().get('raw', 'no response')}",
        )

    reply = filters.pop("reply", "Here are some providers that match your needs.")
    language = filters.pop("language", None)  # stored but not yet a DB column

    # 2. Apply filters and fetch providers
    specialty = filters.get("specialty")
    insurance = filters.get("insurance")
    telehealth = filters.get("telehealth")
    zip_code = filters.get("zip_code")
    max_distance_miles = filters.get("max_distance_miles")

    query = db.query(models.Provider)
    query = apply_filters(
        query,
        specialty=specialty,
        insurance=insurance,
        telehealth=telehealth,
        zip_code=zip_code,
        max_distance_miles=max_distance_miles,
    )
    providers = query.all()

    # 3. Fetch FHIR patient context if patient_id provided
    patient_conditions = None
    patient_coverage = None
    if request.patient_id:
        try:
            patient_conditions = fhir_client.get_patient_conditions(request.patient_id)
        except Exception:
            pass
        try:
            patient_coverage = fhir_client.get_patient_coverage(request.patient_id)
        except Exception:
            pass

    # 4. Rank providers
    distance_map: dict[int, float] = {}
    ranked = rank_providers(
        providers,
        patient_conditions=patient_conditions,
        patient_coverage=patient_coverage,
        insurance=insurance,
        specialty=specialty,
        distance_map=distance_map,
    )

    # 5. Build response
    results = [
        schemas.RankedProviderOut(
            id=p.id,
            name=p.name,
            specialty=p.specialty,
            city=p.city,
            state=p.state,
            zip_code=p.zip_code,
            phone=p.phone,
            insurance_accepted=p.insurance_accepted,
            telehealth=p.telehealth,
            latitude=p.latitude,
            longitude=p.longitude,
            fhir_id=p.fhir_id,
            rank_score=score,
            distance_miles=distance_map.get(p.id),
        )
        for p, score in ranked[:10]
    ]

    if not results:
        reply = "I couldn't find any providers matching those criteria. Try broadening your search."

    return ChatResponse(reply=reply, filters=filters, providers=results)
