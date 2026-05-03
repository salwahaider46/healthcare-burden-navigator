import json
import os
import re
from typing import Optional

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import fhir_client, models, schemas
from app.database import get_db
from app.services.filtering import apply_filters, compute_distance_miles
from app.services.ranking import rank_providers

router = APIRouter(prefix="/chat", tags=["chatbot"])

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
_model = genai.GenerativeModel("gemini-2.0-flash-lite")

EXTRACT_PROMPT = """
You are a healthcare search assistant. Extract structured search filters from
the user's natural language message and return ONLY a JSON object with these
optional fields (omit fields not mentioned):

{{
  "specialty":          string,   // e.g. "cardiology", "dermatology"
  "insurance":          string,   // insurance plan name
  "telehealth":         boolean,  // true if user wants telehealth
  "zip_code":           string,   // 5-digit zip code
  "max_distance_miles": number,   // numeric miles
  "language":           string,   // preferred language
  "reply":              string    // short friendly acknowledgement (1 sentence)
}}

User message: {message}
"""

# Known specialties and insurance plans for local fallback parsing
_SPECIALTIES = [
    "cardiology", "dermatology", "endocrinology", "family medicine",
    "gastroenterology", "internal medicine", "neurology",
    "obstetrics & gynecology", "obstetrics", "gynecology", "oncology",
    "ophthalmology", "orthopedics", "pediatrics", "psychiatry",
    "pulmonology", "urology",
]

_INSURANCE_PLANS = [
    "medicaid", "medicare", "aetna", "blue cross blue shield", "bcbs",
    "cigna", "humana", "unitedhealth", "unitedhealthcare", "kaiser",
    "kaiser permanente", "tricare",
]


def _extract_filters_local(message: str) -> dict:
    """Keyword-based fallback when Gemini is unavailable."""
    msg = message.lower()
    filters = {}

    # Specialty
    for spec in _SPECIALTIES:
        if spec in msg:
            filters["specialty"] = spec.title()
            break

    # Insurance
    for plan in _INSURANCE_PLANS:
        if plan in msg:
            name = plan.title()
            if plan == "bcbs":
                name = "Blue Cross Blue Shield"
            elif plan in ("unitedhealth", "unitedhealthcare"):
                name = "UnitedHealthcare"
            elif plan == "kaiser":
                name = "Kaiser Permanente"
            filters["insurance"] = name
            break

    # Telehealth
    if "telehealth" in msg or "virtual" in msg or "online" in msg or "remote" in msg:
        filters["telehealth"] = True

    # Zip code
    zip_match = re.search(r"\b(\d{5})\b", message)
    if zip_match:
        filters["zip_code"] = zip_match.group(1)

    # Distance
    dist_match = re.search(r"(\d+)\s*(?:mile|mi)", msg)
    if dist_match:
        filters["max_distance_miles"] = int(dist_match.group(1))

    # Generate reply
    parts = []
    if "specialty" in filters:
        parts.append(filters["specialty"].lower() + " providers")
    else:
        parts.append("providers")
    if "insurance" in filters:
        parts.append(f"accepting {filters['insurance']}")
    if filters.get("telehealth"):
        parts.append("with telehealth")
    if "zip_code" in filters:
        parts.append(f"near {filters['zip_code']}")

    filters["reply"] = f"Searching for {' '.join(parts)}."
    return filters


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
    conversational reply.  Falls back to local keyword parsing if Gemini is
    unavailable.
    """
    # 1. Extract filters from the user message via Gemini (with fallback)
    prompt = EXTRACT_PROMPT.format(message=request.message)
    try:
        gemini_response = _model.generate_content(prompt)
        raw = gemini_response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        filters = json.loads(raw.strip())
    except Exception:
        # Fallback: extract filters locally via keyword matching
        filters = _extract_filters_local(request.message)

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
