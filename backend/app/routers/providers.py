from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app import models, schemas, fhir_client

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/search", response_model=List[schemas.ProviderOut])
def search_providers(
    name: Optional[str] = Query(None, description="Provider name (partial match)"),
    specialty: Optional[str] = Query(None, description="Medical specialty"),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    insurance: Optional[str] = Query(None, description="Insurance plan accepted"),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    query = db.query(models.Provider)

    if name:
        query = query.filter(models.Provider.name.ilike(f"%{name}%"))
    if specialty:
        query = query.filter(models.Provider.specialty.ilike(f"%{specialty}%"))
    if city:
        query = query.filter(models.Provider.city.ilike(f"%{city}%"))
    if state:
        query = query.filter(models.Provider.state.ilike(f"%{state}%"))
    if zip_code:
        query = query.filter(models.Provider.zip_code == zip_code)
    if insurance:
        query = query.filter(
            models.Provider.insurance_accepted.ilike(f"%{insurance}%")
        )

    return query.offset(offset).limit(limit).all()


@router.get("/{provider_id}", response_model=schemas.ProviderOut)
def get_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.get("/{provider_id}/details")
def get_provider_details(provider_id: int, db: Session = Depends(get_db)):
    """Returns provider record merged with their FHIR Practitioner data."""
    provider = db.query(models.Provider).filter(models.Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    result = {
        "id": provider.id,
        "name": provider.name,
        "specialty": provider.specialty,
        "city": provider.city,
        "state": provider.state,
        "zip_code": provider.zip_code,
        "phone": provider.phone,
        "insurance_accepted": provider.insurance_accepted,
        "fhir_data": None,
    }

    if provider.fhir_id:
        try:
            result["fhir_data"] = fhir_client.get_practitioner(provider.fhir_id)
        except Exception:
            result["fhir_data"] = {"error": "Could not retrieve FHIR data"}

    return result
