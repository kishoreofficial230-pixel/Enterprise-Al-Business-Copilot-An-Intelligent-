from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.customer import Customer
from app.models.sales import Sale


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    # =====================================================
    # TOTAL CUSTOMERS
    # =====================================================

    total_customers = (
        db.query(Customer)
        .count()
    )


    # =====================================================
    # TOTAL SALES / ORDERS
    # =====================================================

    total_orders = (
        db.query(Sale)
        .count()
    )


    # =====================================================
    # TOTAL REVENUE
    # =====================================================

    total_revenue = (
        db.query(
            func.coalesce(
                func.sum(Sale.amount),
                0
            )
        )
        .scalar()
    )


    # =====================================================
    # TOTAL QUANTITY SOLD
    # =====================================================

    total_quantity = (
        db.query(
            func.coalesce(
                func.sum(Sale.quantity),
                0
            )
        )
        .scalar()
    )


    # =====================================================
    # AVERAGE ORDER VALUE
    # =====================================================

    if total_orders > 0:
        average_order_value = (
            float(total_revenue) / total_orders
        )
    else:
        average_order_value = 0


    # =====================================================
    # ACTIVE CUSTOMERS
    # =====================================================

    # Current customer table structure may not contain
    # an active/inactive field, so for now all existing
    # customers are treated as active.

    active_customers = total_customers
    inactive_customers = 0


    # =====================================================
    # NEW CUSTOMERS
    # =====================================================

    new_customers = total_customers


    # =====================================================
    # RETURN DASHBOARD DATA
    # =====================================================

    return {

        "message": "Dashboard data fetched successfully",

        "user": {
            "user_id": current_user["sub"],
            "email": current_user["email"],
            "role": current_user["role"]
        },

        "kpis": {

            "total_revenue": float(total_revenue),

            "total_sales": total_orders,

            "total_customers": total_customers,

            "average_order_value": round(
                average_order_value,
                2
            ),

            "total_quantity": total_quantity
        },

        "customers": {

            "total_customers": total_customers,

            "active_customers": active_customers,

            "inactive_customers": inactive_customers,

            "new_customers": new_customers
        }
    }