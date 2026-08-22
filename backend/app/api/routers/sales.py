from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.sales import Sale
from app.schemas.sales import SaleCreate, SaleResponse


router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


# Add Sale
@router.post("/", response_model=SaleResponse)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db)
):
    new_sale = Sale(
        product_name=sale.product_name,
        category=sale.category,
        quantity=sale.quantity,
        amount=sale.amount,
        customer_name=sale.customer_name
    )

    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)

    return new_sale


# Get All Sales
@router.get("/", response_model=list[SaleResponse])
def get_sales(
    db: Session = Depends(get_db)
):
    sales = db.query(Sale).all()

    return sales


# Get Single Sale
@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if not sale:
        raise HTTPException(
            status_code=404,
            detail="Sale not found"
        )

    return sale


# Delete Sale
@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db)
):
    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if not sale:
        raise HTTPException(
            status_code=404,
            detail="Sale not found"
        )

    db.delete(sale)
    db.commit()

    return {
        "message": "Sale deleted successfully"
    }