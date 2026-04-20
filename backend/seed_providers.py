"""
Seed script — creates the providers table and inserts sample data.

Usage:
    python seed_providers.py

Requires DATABASE_URL env var or defaults to:
    postgresql://postgres:password@localhost:5432/healthcare_nav

If using the fhir_docker_setup Postgres, first create the database:
    docker exec -it fhir_postgres psql -U fhir_user -d fhir_demo \
        -c "CREATE DATABASE healthcare_nav;"

Then override the connection string:
    DATABASE_URL=postgresql://fhir_user:fhir_password@localhost:5432/healthcare_nav \
        python seed_providers.py
"""

import os
import sys

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.database import Base
from app.models import Provider

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/healthcare_nav",
)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


SAMPLE_PROVIDERS = [
    dict(
        name="Dr. Maria Santos",
        specialty="Family Medicine",
        city="Atlanta",
        state="GA",
        zip_code="30318",
        phone="(404) 555-0101",
        insurance_accepted="Medicaid, Medicare, Aetna, Blue Cross Blue Shield",
        telehealth=True,
        latitude=33.7810,
        longitude=-84.4230,
    ),
    dict(
        name="Dr. James Chen",
        specialty="Cardiology",
        city="Atlanta",
        state="GA",
        zip_code="30308",
        phone="(404) 555-0102",
        insurance_accepted="Medicare, UnitedHealthcare, Cigna",
        telehealth=True,
        latitude=33.7712,
        longitude=-84.3715,
    ),
    dict(
        name="Dr. Fatima Al-Rashid",
        specialty="Endocrinology",
        city="Decatur",
        state="GA",
        zip_code="30030",
        phone="(404) 555-0103",
        insurance_accepted="Medicaid, Humana, Aetna",
        telehealth=False,
        latitude=33.7748,
        longitude=-84.2963,
    ),
    dict(
        name="Dr. Robert Kim",
        specialty="Psychiatry",
        city="Atlanta",
        state="GA",
        zip_code="30309",
        phone="(404) 555-0104",
        insurance_accepted="Medicaid, Medicare, Blue Cross Blue Shield, Cigna",
        telehealth=True,
        latitude=33.7930,
        longitude=-84.3880,
    ),
    dict(
        name="Dr. Angela Brooks",
        specialty="Pediatrics",
        city="East Point",
        state="GA",
        zip_code="30344",
        phone="(404) 555-0105",
        insurance_accepted="Medicaid, Medicare, Aetna",
        telehealth=True,
        latitude=33.6795,
        longitude=-84.4393,
    ),
    dict(
        name="Dr. David Okafor",
        specialty="Internal Medicine",
        city="Atlanta",
        state="GA",
        zip_code="30312",
        phone="(404) 555-0106",
        insurance_accepted="Medicaid, UnitedHealthcare, Humana, Tricare",
        telehealth=False,
        latitude=33.7415,
        longitude=-84.3717,
    ),
    dict(
        name="Dr. Sarah Patel",
        specialty="Obstetrics & Gynecology",
        city="Marietta",
        state="GA",
        zip_code="30060",
        phone="(770) 555-0107",
        insurance_accepted="Blue Cross Blue Shield, Cigna, Kaiser Permanente",
        telehealth=True,
        latitude=33.9526,
        longitude=-84.5499,
    ),
    dict(
        name="Dr. Michael Thompson",
        specialty="Orthopedics",
        city="Sandy Springs",
        state="GA",
        zip_code="30328",
        phone="(404) 555-0108",
        insurance_accepted="Medicare, UnitedHealthcare, Aetna",
        telehealth=False,
        latitude=33.9304,
        longitude=-84.3733,
    ),
    dict(
        name="Dr. Lisa Nguyen",
        specialty="Dermatology",
        city="Atlanta",
        state="GA",
        zip_code="30305",
        phone="(404) 555-0109",
        insurance_accepted="Medicaid, Blue Cross Blue Shield, Humana",
        telehealth=True,
        latitude=33.8340,
        longitude=-84.3880,
    ),
    dict(
        name="Dr. Carlos Rivera",
        specialty="Neurology",
        city="Roswell",
        state="GA",
        zip_code="30075",
        phone="(770) 555-0110",
        insurance_accepted="Medicare, Cigna, Tricare",
        telehealth=False,
        latitude=34.0234,
        longitude=-84.3613,
    ),
    dict(
        name="Dr. Amina Hassan",
        specialty="Pulmonology",
        city="Atlanta",
        state="GA",
        zip_code="30322",
        phone="(404) 555-0111",
        insurance_accepted="Medicaid, Medicare, Aetna, UnitedHealthcare",
        telehealth=True,
        latitude=33.7963,
        longitude=-84.3228,
    ),
    dict(
        name="Dr. Kevin Wright",
        specialty="Gastroenterology",
        city="Lawrenceville",
        state="GA",
        zip_code="30046",
        phone="(770) 555-0112",
        insurance_accepted="Blue Cross Blue Shield, Humana, Cigna",
        telehealth=False,
        latitude=33.9562,
        longitude=-83.9880,
    ),
    dict(
        name="Dr. Elena Vasquez",
        specialty="Family Medicine",
        city="College Park",
        state="GA",
        zip_code="30337",
        phone="(404) 555-0113",
        insurance_accepted="Medicaid, Medicare, Uninsured / Self-Pay",
        telehealth=True,
        latitude=33.6534,
        longitude=-84.4494,
    ),
    dict(
        name="Dr. Andrew Park",
        specialty="Oncology",
        city="Atlanta",
        state="GA",
        zip_code="30342",
        phone="(404) 555-0114",
        insurance_accepted="Medicare, UnitedHealthcare, Blue Cross Blue Shield",
        telehealth=False,
        latitude=33.8668,
        longitude=-84.3599,
    ),
    dict(
        name="Dr. Priya Sharma",
        specialty="Psychiatry",
        city="Smyrna",
        state="GA",
        zip_code="30080",
        phone="(770) 555-0115",
        insurance_accepted="Medicaid, Aetna, Cigna, Kaiser Permanente",
        telehealth=True,
        latitude=33.8839,
        longitude=-84.5144,
    ),
    dict(
        name="Dr. Thomas Greene",
        specialty="Urology",
        city="Duluth",
        state="GA",
        zip_code="30096",
        phone="(770) 555-0116",
        insurance_accepted="Medicare, Humana, Tricare",
        telehealth=False,
        latitude=34.0029,
        longitude=-84.1446,
    ),
    dict(
        name="Dr. Jennifer Lawson",
        specialty="Ophthalmology",
        city="Atlanta",
        state="GA",
        zip_code="30324",
        phone="(404) 555-0117",
        insurance_accepted="Medicaid, Blue Cross Blue Shield, UnitedHealthcare",
        telehealth=False,
        latitude=33.8176,
        longitude=-84.3568,
    ),
    dict(
        name="Dr. Marcus Johnson",
        specialty="Cardiology",
        city="Morrow",
        state="GA",
        zip_code="30260",
        phone="(770) 555-0118",
        insurance_accepted="Medicaid, Medicare, Aetna, Uninsured / Self-Pay",
        telehealth=True,
        latitude=33.5832,
        longitude=-84.3397,
    ),
    dict(
        name="Dr. Rachel Stein",
        specialty="Endocrinology",
        city="Alpharetta",
        state="GA",
        zip_code="30009",
        phone="(770) 555-0119",
        insurance_accepted="Cigna, UnitedHealthcare, Kaiser Permanente",
        telehealth=True,
        latitude=34.0654,
        longitude=-84.2941,
    ),
    dict(
        name="Dr. William Davis",
        specialty="Internal Medicine",
        city="Atlanta",
        state="GA",
        zip_code="30316",
        phone="(404) 555-0120",
        insurance_accepted="Medicaid, Medicare, Humana, Uninsured / Self-Pay",
        telehealth=True,
        latitude=33.7224,
        longitude=-84.3400,
    ),
]


def seed():
    print(f"Connecting to: {DATABASE_URL}")

    # Create all tables
    Base.metadata.create_all(engine)
    print("Tables created (or already exist).")

    session = Session()

    existing = session.query(Provider).count()
    if existing > 0:
        print(f"Database already has {existing} providers. Skipping seed.")
        session.close()
        return

    for data in SAMPLE_PROVIDERS:
        session.add(Provider(**data))

    session.commit()
    count = session.query(Provider).count()
    print(f"Seeded {count} providers successfully.")
    session.close()


if __name__ == "__main__":
    seed()
