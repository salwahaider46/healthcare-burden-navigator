from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app import models, schemas, fhir_client
from app.services.filtering import apply_filters, compute_distance_miles
from app.services.ranking import rank_providers

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/recommendations", response_model=List[schemas.RankedProviderOut])
def get_recommendations(
    specialty: Optional[str] = Query(None, description="Medical specialty"),
    insurance: Optional[str] = Query(None, description="Insurance plan accepted"),
    telehealth: Optional[bool] = Query(None, description="Telehealth availability"),
    zip_code: Optional[str] = Query(None, description="Patient zip code for distance filtering"),
    max_distance_miles: Optional[float] = Query(None, description="Maximum distance in miles"),
    user_lat: Optional[float] = Query(None, description="Patient latitude"),
    user_lon: Optional[float] = Query(None, description="Patient longitude"),
    patient_id: Optional[str] = Query(None, description="FHIR patient ID for care-need inference"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    """
    Return ranked provider recommendations based on filters and patient context.

    Filtering (Ahmet) and ranking (Vivek) logic live in app/services/.
    FHIR patient data (Sitong) is fetched here when patient_id is provided.
    """
    query = db.query(models.Provider)
    query = apply_filters(
        query,
        specialty=specialty,
        insurance=insurance,
        telehealth=telehealth,
        zip_code=zip_code,
        max_distance_miles=max_distance_miles,
        user_lat=user_lat,
        user_lon=user_lon,
    )
    providers = query.all()

    # Fetch FHIR patient data for ranking context (Sitong's integration)
    patient_conditions = None
    patient_coverage = None
    if patient_id:
        try:
            patient_conditions = fhir_client.get_patient_conditions(patient_id=patient_id)
        except Exception:
            patient_conditions = None
        try:
            patient_coverage = fhir_client.get_patient_coverage(patient_id=patient_id)
        except Exception:
            patient_coverage = None

    # Pre-compute distances when coordinates are available
    distance_map: dict[int, float] = {}
    if user_lat is not None and user_lon is not None:
        for p in providers:
            if p.latitude is not None and p.longitude is not None:
                distance_map[p.id] = compute_distance_miles(
                    user_lat, user_lon, p.latitude, p.longitude
                )

    ranked = rank_providers(
        providers,
        patient_conditions=patient_conditions,
        patient_coverage=patient_coverage,
        user_lat=user_lat,
        user_lon=user_lon,
        insurance=insurance,
        specialty=specialty,
        distance_map=distance_map,
    )

    results = []
    for provider, score in ranked[:limit]:
        out = schemas.RankedProviderOut(
            id=provider.id,
            name=provider.name,
            specialty=provider.specialty,
            city=provider.city,
            state=provider.state,
            zip_code=provider.zip_code,
            phone=provider.phone,
            insurance_accepted=provider.insurance_accepted,
            telehealth=provider.telehealth,
            latitude=provider.latitude,
            longitude=provider.longitude,
            fhir_id=provider.fhir_id,
            rank_score=score,
            distance_miles=distance_map.get(provider.id),
        )
        results.append(out)
    return results


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
