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


def radius_filter_is_active(
    max_distance_miles: Optional[float],
    user_lat: Optional[float],
    user_lon: Optional[float],
) -> bool:
    """True when Haversine radius filtering should run (miles, both user coordinates)."""
    if user_lat is None or user_lon is None:
        return False
    if max_distance_miles is None:
        return False
    if max_distance_miles <= 0:
        return False
    return True


def build_distance_map_and_apply_radius(
    providers: list[models.Provider],
    *,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    max_distance_miles: Optional[float] = None,
) -> tuple[list[models.Provider], dict[int, float]]:
    """
    When user_lat/user_lon are set, compute Haversine distance (miles) for each
    provider with coordinates. If max_distance_miles is set (> 0), drop providers
    outside the radius or without coordinates (cannot verify they are inside).
    """
    distance_map: dict[int, float] = {}
    if user_lat is None or user_lon is None:
        return providers, distance_map

    for p in providers:
        if p.latitude is not None and p.longitude is not None:
            distance_map[p.id] = compute_distance_miles(
                user_lat, user_lon, p.latitude, p.longitude
            )

    if not radius_filter_is_active(max_distance_miles, user_lat, user_lon):
        return providers, distance_map

    assert max_distance_miles is not None
    filtered = [
        p
        for p in providers
        if p.id in distance_map and distance_map[p.id] <= max_distance_miles
    ]
    return filtered, distance_map


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

    # Exact ZIP match only when we are not using lat/lon + max_distance (miles).
    # Requires both user_lat and user_lon to skip ZIP fallback; one alone is treated as missing.
    if zip_code and not radius_filter_is_active(max_distance_miles, user_lat, user_lon):
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
