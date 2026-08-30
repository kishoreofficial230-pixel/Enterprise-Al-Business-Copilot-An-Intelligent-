from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime

from app.database.database import Base


class Sale(Base):
    __tablename__ = "sales"

    # =====================================================
    # BASIC SALE DETAILS
    # =====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    invoice_number = Column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )

    product_name = Column(
        String(255),
        nullable=False
    )

    hsn_code = Column(
        String(50),
        nullable=True
    )

    category = Column(
        String(100),
        nullable=True
    )

    quantity = Column(
        Integer,
        nullable=False
    )


    # =====================================================
    # CUSTOMER DETAILS
    # =====================================================

    customer_name = Column(
        String(255),
        nullable=True
    )

    customer_phone = Column(
        String(20),
        nullable=True
    )

    customer_address = Column(
        String(500),
        nullable=True
    )

    gstin = Column(
        String(50),
        nullable=True
    )


    # =====================================================
    # PRICE DETAILS
    # =====================================================

    unit_price = Column(
        Float,
        nullable=True
    )

    taxable_amount = Column(
        Float,
        nullable=True
    )

    gst_percent = Column(
        Float,
        nullable=False,
        default=0.0
    )

    cgst = Column(
        Float,
        nullable=False,
        default=0.0
    )

    sgst = Column(
        Float,
        nullable=False,
        default=0.0
    )

    igst = Column(
        Float,
        nullable=False,
        default=0.0
    )

    final_amount = Column(
        Float,
        nullable=True
    )


    # =====================================================
    # EXISTING AMOUNT FIELD
    # =====================================================
    #
    # IMPORTANT:
    # Existing Dashboard, Analytics, AI Copilot and
    # Machine Learning code already uses "amount".
    #
    # So we are keeping this field.
    # Later while creating a sale:
    #
    # amount = final_amount
    #
    # This prevents existing features from breaking.
    # =====================================================

    amount = Column(
        Float,
        nullable=False
    )


    # =====================================================
    # SALE DATE
    # =====================================================

    sale_date = Column(
        DateTime,
        default=datetime.utcnow
    )