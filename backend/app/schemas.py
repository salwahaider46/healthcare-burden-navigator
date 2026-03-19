from pydantic import BaseModel
from typing import Optional


class ProviderBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    insurance_accepted: Optional[str] = None
    fhir_id: Optional[str] = None


class ProviderOut(ProviderBase):
    id: int

    class Config:
        from_attributes = True
