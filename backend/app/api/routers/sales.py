import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.sales import Sale
from app.schemas.sales import SaleCreate, SaleResponse


router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


# =====================================================
# GENERATE INVOICE NUMBER
# =====================================================

def generate_invoice_number(
    db: Session
):
    invoice_rows = (
        db.query(
            Sale.invoice_number
        )
        .filter(
            Sale.invoice_number.isnot(
                None
            )
        )
        .all()
    )

    highest_number = 0

    for row in invoice_rows:

        invoice_number = row[0]

        if not invoice_number:
            continue

        match = re.fullmatch(
            r"INV-(\d+)",
            str(
                invoice_number
            ).strip(),
            flags=re.IGNORECASE
        )

        if match:

            number = int(
                match.group(1)
            )

            highest_number = max(
                highest_number,
                number
            )

    next_number = (
        highest_number + 1
    )

    return (
        f"INV-{next_number:06d}"
    )


# =====================================================
# CALCULATE GST
# =====================================================

def calculate_sale_amounts(
    quantity: int,
    unit_price: float,
    gst_percent: float,
    tax_type: str
):
    quantity = int(
        quantity
    )

    unit_price = float(
        unit_price
    )

    gst_percent = float(
        gst_percent or 0
    )

    taxable_amount = round(
        quantity * unit_price,
        2
    )

    total_gst_amount = round(
        taxable_amount
        * gst_percent
        / 100,
        2
    )

    cgst = 0.0
    sgst = 0.0
    igst = 0.0

    if tax_type == "IGST":

        igst = round(
            total_gst_amount,
            2
        )

    else:

        cgst = round(
            total_gst_amount / 2,
            2
        )

        sgst = round(
            total_gst_amount - cgst,
            2
        )

    final_amount = round(
        taxable_amount
        + total_gst_amount,
        2
    )

    return {
        "taxable_amount":
            taxable_amount,

        "cgst":
            cgst,

        "sgst":
            sgst,

        "igst":
            igst,

        "final_amount":
            final_amount,
    }


# =====================================================
# ADD SALE
# =====================================================

@router.post(
    "/",
    response_model=SaleResponse
)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(
        get_db
    )
):
    calculations = (
        calculate_sale_amounts(
            quantity=sale.quantity,
            unit_price=sale.unit_price,
            gst_percent=sale.gst_percent,
            tax_type=sale.tax_type
        )
    )

    # Try a few times in the unlikely event that
    # two sales receive the same invoice number.
    for attempt in range(3):

        invoice_number = (
            generate_invoice_number(
                db
            )
        )

        new_sale = Sale(

            # Invoice
            invoice_number=
                invoice_number,

            # Product
            product_name=
                sale.product_name,

            hsn_code=
                sale.hsn_code,

            category=
                sale.category,

            quantity=
                sale.quantity,

            # Customer
            customer_name=
                sale.customer_name,

            customer_phone=
                sale.customer_phone,

            customer_address=
                sale.customer_address,

            gstin=
                sale.gstin,

            # Price
            unit_price=
                sale.unit_price,

            taxable_amount=
                calculations[
                    "taxable_amount"
                ],

            gst_percent=
                sale.gst_percent,

            cgst=
                calculations[
                    "cgst"
                ],

            sgst=
                calculations[
                    "sgst"
                ],

            igst=
                calculations[
                    "igst"
                ],

            final_amount=
                calculations[
                    "final_amount"
                ],

            # Existing field used by
            # Dashboard / Analytics / AI / ML
            amount=
                calculations[
                    "final_amount"
                ],

            # Date
            sale_date=
                sale.sale_date
                or datetime.utcnow()
        )

        try:

            db.add(
                new_sale
            )

            db.commit()

            db.refresh(
                new_sale
            )

            return new_sale

        except IntegrityError:

            db.rollback()

            if attempt == 2:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Unable to generate "
                        "a unique invoice number"
                    )
                )


# =====================================================
# GET ALL SALES
# =====================================================

@router.get(
    "/",
    response_model=list[
        SaleResponse
    ]
)
def get_sales(
    db: Session = Depends(
        get_db
    )
):
    sales = (
        db.query(
            Sale
        )
        .order_by(
            Sale.sale_date.asc(),
            Sale.id.asc()
        )
        .all()
    )

    return sales


# =====================================================
# GET SINGLE SALE
# =====================================================

@router.get(
    "/{sale_id}",
    response_model=SaleResponse
)
def get_sale(
    sale_id: int,
    db: Session = Depends(
        get_db
    )
):
    sale = (
        db.query(
            Sale
        )
        .filter(
            Sale.id == sale_id
        )
        .first()
    )

    if not sale:

        raise HTTPException(
            status_code=404,
            detail="Sale not found"
        )

    return sale


# =====================================================
# DELETE SALE
# =====================================================

@router.delete(
    "/{sale_id}"
)
def delete_sale(
    sale_id: int,
    db: Session = Depends(
        get_db
    )
):
    sale = (
        db.query(
            Sale
        )
        .filter(
            Sale.id == sale_id
        )
        .first()
    )

    if not sale:

        raise HTTPException(
            status_code=404,
            detail="Sale not found"
        )

    db.delete(
        sale
    )

    db.commit()

    return {
        "message":
            "Sale deleted successfully"
    }