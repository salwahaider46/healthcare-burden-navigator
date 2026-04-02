from sqlalchemy import Boolean, Column, Float, Integer, String
from app.database import Base


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String, index=True)
    city = Column(String, index=True)
    state = Column(String, index=True)
    zip_code = Column(String)
    phone = Column(String)
    insurance_accepted = Column(String)   # comma-separated list
    telehealth = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    fhir_id = Column(String)              # links to FHIR Practitioner resource
