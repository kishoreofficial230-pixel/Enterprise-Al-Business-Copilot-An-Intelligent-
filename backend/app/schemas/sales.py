from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SaleCreate(BaseModel):
    product_name: str
    category: Optional[str] = None
    quantity: int
    amount: float
    customer_name: Optional[str] = None


class SaleResponse(BaseModel):
    id: int
    product_name: str
    category: Optional[str]
    quantity: int
    amount: float
    customer_name: Optional[str]
    sale_date: datetime

    class Config:
        from_attributes = True