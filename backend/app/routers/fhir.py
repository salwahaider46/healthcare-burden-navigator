from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app import fhir_client

router = APIRouter(prefix="/fhir", tags=["fhir"])


@router.get("/practitioners")
def search_practitioners(
    name: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
):
    try:
        return fhir_client.search_practitioners(name=name, specialty=specialty)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FHIR server error: {str(e)}")


@router.get("/practitioners/{fhir_id}")
def get_practitioner(fhir_id: str):
    try:
        return fhir_client.get_practitioner(fhir_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FHIR server error: {str(e)}")


@router.get("/conditions")
def search_conditions(
    subject: Optional[str] = Query(None, description="Patient ID"),
    code: Optional[str] = Query(None, description="Condition code (SNOMED/ICD)"),
):
    try:
        return fhir_client.search_conditions(subject=subject, code=code)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FHIR server error: {str(e)}")


@router.get("/encounters")
def search_encounters(
    subject: Optional[str] = Query(None, description="Patient ID"),
    practitioner: Optional[str] = Query(None, description="Practitioner ID"),
):
    try:
        return fhir_client.search_encounters(subject=subject, practitioner=practitioner)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FHIR server error: {str(e)}")


@router.get("/coverage")
def search_coverage(
    beneficiary: Optional[str] = Query(None, description="Patient ID"),
):
    try:
        return fhir_client.search_coverage(beneficiary=beneficiary)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FHIR server error: {str(e)}")
