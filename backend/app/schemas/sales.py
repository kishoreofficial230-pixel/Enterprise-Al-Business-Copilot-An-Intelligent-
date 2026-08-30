from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


# =====================================================
# CREATE SALE SCHEMA
# =====================================================

class SaleCreate(BaseModel):

    # Product Details
    product_name: str = Field(
        ...,
        min_length=1,
        max_length=255
    )

    hsn_code: Optional[str] = Field(
        default=None,
        max_length=50
    )

    category: Optional[str] = Field(
        default=None,
        max_length=100
    )

    quantity: int = Field(
        ...,
        gt=0
    )


    # =====================================================
    # CUSTOMER DETAILS
    # =====================================================

    customer_name: Optional[str] = Field(
        default=None,
        max_length=255
    )

    customer_phone: Optional[str] = Field(
        default=None,
        max_length=20
    )

    customer_address: Optional[str] = Field(
        default=None,
        max_length=500
    )

    gstin: Optional[str] = Field(
        default=None,
        max_length=50
    )


    # =====================================================
    # PRICE + GST DETAILS
    # =====================================================

    unit_price: float = Field(
        ...,
        ge=0
    )

    gst_percent: float = Field(
        default=0.0,
        ge=0,
        le=100
    )

    tax_type: Literal[
        "CGST_SGST",
        "IGST"
    ] = "CGST_SGST"


    # =====================================================
    # OPTIONAL SALE DATE
    # =====================================================

    sale_date: Optional[datetime] = None


# =====================================================
# SALE RESPONSE SCHEMA
# =====================================================

class SaleResponse(BaseModel):

    id: int

    invoice_number: Optional[str] = None

    product_name: str

    hsn_code: Optional[str] = None

    category: Optional[str] = None

    quantity: int


    # =====================================================
    # CUSTOMER DETAILS
    # =====================================================

    customer_name: Optional[str] = None

    customer_phone: Optional[str] = None

    customer_address: Optional[str] = None

    gstin: Optional[str] = None


    # =====================================================
    # PRICE DETAILS
    # =====================================================

    unit_price: Optional[float] = None

    taxable_amount: Optional[float] = None

    gst_percent: float = 0.0

    cgst: float = 0.0

    sgst: float = 0.0

    igst: float = 0.0

    final_amount: Optional[float] = None


    # =====================================================
    # EXISTING AMOUNT
    # =====================================================

    amount: float


    # =====================================================
    # DATE
    # =====================================================

    sale_date: datetime


    model_config = ConfigDict(
        from_attributes=True
    )