import os
import httpx
from typing import Optional

FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8081/fhir")


def _get(path: str, params: dict = None):
    url = f"{FHIR_BASE_URL}/{path}"
    headers = {"Accept": "application/fhir+json"}
    response = httpx.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def get_practitioner(fhir_id: str) -> dict:
    return _get(f"Practitioner/{fhir_id}")


def search_practitioners(name: Optional[str] = None, specialty: Optional[str] = None) -> dict:
    params = {}
    if name:
        params["name"] = name
    if specialty:
        params["specialty"] = specialty
    return _get("Practitioner", params=params)


def search_conditions(subject: Optional[str] = None, code: Optional[str] = None) -> dict:
    params = {}
    if subject:
        params["subject"] = subject
    if code:
        params["code"] = code
    return _get("Condition", params=params)


def search_encounters(subject: Optional[str] = None, practitioner: Optional[str] = None) -> dict:
    params = {}
    if subject:
        params["subject"] = subject
    if practitioner:
        params["participant"] = practitioner
    return _get("Encounter", params=params)


def search_coverage(beneficiary: Optional[str] = None) -> dict:
    params = {}
    if beneficiary:
        params["beneficiary"] = beneficiary
    return _get("Coverage", params=params)
