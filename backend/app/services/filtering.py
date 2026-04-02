"""
Provider filtering logic — Sprint 4 (Ahmet)

apply_filters() is called by the recommendations endpoint to narrow down
providers before ranking. Add insurance, specialty, telehealth, and
distance logic here.
"""

import math
from typing import Optional

from sqlalchemy.orm import Query

from app import models


def apply_filters(
    query: Query,
    specialty: Optional[str] = None,
    insurance: Optional[str] = None,
    telehealth: Optional[bool] = None,
    zip_code: Optional[str] = None,
    max_distance_miles: Optional[float] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
) -> Query:
    """Return a filtered SQLAlchemy query based on the provided criteria."""

    if specialty:
        query = query.filter(models.Provider.specialty.ilike(f"%{specialty}%"))

    if insurance:
        query = query.filter(
            models.Provider.insurance_accepted.ilike(f"%{insurance}%")
        )

    if telehealth is not None:
        query = query.filter(models.Provider.telehealth == telehealth)

    if zip_code and (max_distance_miles is None or user_lat is None):
        # Fallback: exact zip match when no coordinates are available.
        # TODO (Ahmet): replace with geocoding + distance radius query.
        query = query.filter(models.Provider.zip_code == zip_code)

    return query


def compute_distance_miles(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Haversine distance between two lat/lon points in miles."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
