"""
Burden-reduction ranking algorithm — Sprint 4 (Vivek)

rank_providers() is called by the recommendations endpoint after filtering.
It receives the provider list and optional FHIR patient data (conditions,
coverage) inferred by Sitong's integration, and returns providers sorted
by descending rank_score.

Scoring weights below are placeholders — replace with the real algorithm.
"""

from typing import Optional

from app import models


# Weights — TODO (Vivek): tune based on burden-reduction research
WEIGHT_TELEHEALTH = 10.0
WEIGHT_INSURANCE_MATCH = 20.0
WEIGHT_DISTANCE = 15.0     # applied as a penalty per 10 miles
WEIGHT_SPECIALTY_MATCH = 25.0


def rank_providers(
    providers: list[models.Provider],
    patient_conditions: Optional[list[dict]] = None,
    patient_coverage: Optional[list[dict]] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
    insurance: Optional[str] = None,
    specialty: Optional[str] = None,
    distance_map: Optional[dict[int, float]] = None,
) -> list[tuple[models.Provider, float]]:
    """
    Score each provider and return a list of (provider, score) tuples
    sorted by descending score.

    Args:
        providers:          Filtered provider records from the DB.
        patient_conditions: FHIR Condition resources for the patient (Sitong).
        patient_coverage:   FHIR Coverage resources for the patient (Sitong).
        user_lat/user_lon:  Patient coordinates for distance scoring.
        insurance:          Insurance filter value, used for match bonus.
        specialty:          Specialty filter value, used for match bonus.
        distance_map:       provider.id → distance in miles (pre-computed).
    """
    scored = []
    for provider in providers:
        score = _base_score(
            provider,
            insurance=insurance,
            specialty=specialty,
            distance_map=distance_map,
        )
        # TODO (Vivek): incorporate patient_conditions and patient_coverage
        # to boost providers that match the patient's inferred care needs.
        scored.append((provider, round(score, 2)))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _base_score(
    provider: models.Provider,
    insurance: Optional[str],
    specialty: Optional[str],
    distance_map: Optional[dict[int, float]],
) -> float:
    score = 0.0

    if provider.telehealth:
        score += WEIGHT_TELEHEALTH

    if insurance and provider.insurance_accepted:
        if insurance.lower() in provider.insurance_accepted.lower():
            score += WEIGHT_INSURANCE_MATCH

    if specialty and provider.specialty:
        if specialty.lower() in provider.specialty.lower():
            score += WEIGHT_SPECIALTY_MATCH

    if distance_map and provider.id in distance_map:
        miles = distance_map[provider.id]
        penalty = (miles / 10) * WEIGHT_DISTANCE
        score -= penalty

    return max(score, 0.0)
