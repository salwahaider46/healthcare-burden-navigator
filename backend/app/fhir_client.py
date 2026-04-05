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


def get_patient_conditions(patient_id: str, code: Optional[str] = None) -> list[dict]:
    """
    Return normalized Condition resources for a patient.

    The HAPI search parameter may require either `123` or `Patient/123`
    depending on data shape/config. We try both forms and merge results.
    """
    normalized: list[dict] = []
    seen_ids: set[str] = set()

    for subject in _patient_reference_candidates(patient_id):
        bundle = search_conditions(subject=subject, code=code)
        for resource in _bundle_resources(bundle):
            condition = _normalize_condition_resource(resource)
            condition_id = condition.get("id")
            if condition_id and condition_id in seen_ids:
                continue
            if condition_id:
                seen_ids.add(condition_id)
            normalized.append(condition)

    return normalized


def get_patient_coverage(patient_id: str) -> list[dict]:
    """
    Return normalized Coverage resources for a patient.

    Similar to conditions, we try both `123` and `Patient/123`.
    """
    normalized: list[dict] = []
    seen_ids: set[str] = set()

    for beneficiary in _patient_reference_candidates(patient_id):
        bundle = search_coverage(beneficiary=beneficiary)
        for resource in _bundle_resources(bundle):
            coverage = _normalize_coverage_resource(resource)
            coverage_id = coverage.get("id")
            if coverage_id and coverage_id in seen_ids:
                continue
            if coverage_id:
                seen_ids.add(coverage_id)
            normalized.append(coverage)

    return normalized


def _bundle_resources(bundle: dict) -> list[dict]:
    entries = bundle.get("entry", []) if isinstance(bundle, dict) else []
    resources: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        resource = entry.get("resource", entry)
        if isinstance(resource, dict):
            resources.append(resource)
    return resources


def _patient_reference_candidates(patient_id: str) -> list[str]:
    value = patient_id.strip()
    if not value:
        return []

    if value.startswith("Patient/"):
        bare_id = value.split("/", 1)[1]
        return [value, bare_id] if bare_id else [value]

    return [value, f"Patient/{value}"]


def _normalize_condition_resource(resource: dict) -> dict:
    clinical_status = resource.get("clinicalStatus")
    verification_status = resource.get("verificationStatus")
    code = resource.get("code")

    return {
        "id": resource.get("id"),
        "resource_type": "Condition",
        "subject_reference": _safe_nested_get(resource, "subject", "reference"),
        "code": _extract_code(code, prefer="code"),
        "code_display": _extract_code(code, prefer="display"),
        "code_text": _extract_codeable_concept_text(code),
        "clinical_status": _extract_code(clinical_status, prefer="code")
        or _extract_codeable_concept_text(clinical_status),
        "verification_status": _extract_code(verification_status, prefer="code")
        or _extract_codeable_concept_text(verification_status),
        "onset": resource.get("onsetDateTime")
        or resource.get("recordedDate")
        or resource.get("assertedDate"),
    }


def _normalize_coverage_resource(resource: dict) -> dict:
    type_concept = resource.get("type")
    payor_refs: list[str] = []
    payor_displays: list[str] = []
    for payor in resource.get("payor", []):
        if not isinstance(payor, dict):
            continue
        reference = payor.get("reference")
        display = payor.get("display")
        if reference:
            payor_refs.append(reference)
        if display:
            payor_displays.append(display)

    return {
        "id": resource.get("id"),
        "resource_type": "Coverage",
        "status": resource.get("status"),
        "beneficiary_reference": _safe_nested_get(resource, "beneficiary", "reference"),
        "payor_references": payor_refs,
        "payor_displays": payor_displays,
        "type_code": _extract_code(type_concept, prefer="code"),
        "type_display": _extract_code(type_concept, prefer="display"),
        "type_text": _extract_codeable_concept_text(type_concept),
        "relationship": _extract_codeable_concept_text(resource.get("relationship")),
        "subscriber_id": resource.get("subscriberId"),
    }


def _extract_codeable_concept_text(concept: Optional[dict]) -> Optional[str]:
    if not isinstance(concept, dict):
        return None
    text = concept.get("text")
    if text:
        return text
    coding = concept.get("coding", [])
    if coding and isinstance(coding[0], dict):
        return coding[0].get("display") or coding[0].get("code")
    return None


def _extract_code(concept: Optional[dict], prefer: str) -> Optional[str]:
    if not isinstance(concept, dict):
        return None
    coding = concept.get("coding", [])
    if coding and isinstance(coding[0], dict):
        return coding[0].get(prefer)
    return None


def _safe_nested_get(data: dict, key: str, subkey: str) -> Optional[str]:
    value = data.get(key)
    if not isinstance(value, dict):
        return None
    nested = value.get(subkey)
    return nested if isinstance(nested, str) else None
