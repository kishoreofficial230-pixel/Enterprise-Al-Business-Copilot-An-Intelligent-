from pydantic import BaseModel, EmailStr
from datetime import datetime


class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    status: str = "Active"


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True