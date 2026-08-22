from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.customer import Customer
from app.models.sales import Sale


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/overview")
def analytics_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):

    # =========================================================
    # CURRENT DATE / TIME
    # =========================================================

    now = datetime.now()

    # Start of today
    start_today = datetime(
        now.year,
        now.month,
        now.day
    )

    # Start of tomorrow
    start_tomorrow = start_today + timedelta(days=1)

    # =========================================================
    # START OF CURRENT WEEK
    # Monday = first day of week
    # =========================================================

    start_week = start_today - timedelta(
        days=start_today.weekday()
    )

    # =========================================================
    # START OF CURRENT MONTH
    # =========================================================

    start_month = datetime(
        now.year,
        now.month,
        1
    )


    # =========================================================
    # TOTAL CUSTOMERS
    # =========================================================

    total_customers = (
        db.query(Customer)
        .count()
    )


    # =========================================================
    # TOTAL SALES / ORDERS
    # =========================================================

    total_sales = (
        db.query(Sale)
        .count()
    )


    # =========================================================
    # TOTAL REVENUE
    # =========================================================

    total_revenue = (
        db.query(
            func.coalesce(
                func.sum(Sale.amount),
                0
            )
        )
        .scalar()
    )


    # =========================================================
    # TOTAL QUANTITY
    # =========================================================

    total_quantity = (
        db.query(
            func.coalesce(
                func.sum(Sale.quantity),
                0
            )
        )
        .scalar()
    )


    # =========================================================
    # AVERAGE ORDER VALUE
    # =========================================================

    if total_sales > 0:
        average_order_value = (
            float(total_revenue) / total_sales
        )
    else:
        average_order_value = 0


    # =========================================================
    # CUSTOMER STATUS
    # =========================================================

    active_customers = total_customers
    inactive_customers = 0


    # =========================================================
    # NEW CUSTOMERS
    #
    # If customer model has created_at, use it.
    # Otherwise current total is returned.
    # =========================================================

    try:

        new_customers = (
            db.query(Customer)
            .filter(
                Customer.created_at >= start_month
            )
            .count()
        )

    except Exception:

        new_customers = total_customers


    # =========================================================
    # TODAY SALES REVENUE
    # =========================================================

    today_revenue = (
        db.query(
            func.coalesce(
                func.sum(Sale.amount),
                0
            )
        )
        .filter(
            Sale.sale_date >= start_today,
            Sale.sale_date < start_tomorrow
        )
        .scalar()
    )


    # =========================================================
    # THIS WEEK SALES REVENUE
    # =========================================================

    week_revenue = (
        db.query(
            func.coalesce(
                func.sum(Sale.amount),
                0
            )
        )
        .filter(
            Sale.sale_date >= start_week,
            Sale.sale_date < start_tomorrow
        )
        .scalar()
    )


    # =========================================================
    # THIS MONTH SALES REVENUE
    # =========================================================

    month_revenue = (
        db.query(
            func.coalesce(
                func.sum(Sale.amount),
                0
            )
        )
        .filter(
            Sale.sale_date >= start_month,
            Sale.sale_date < start_tomorrow
        )
        .scalar()
    )


    # =========================================================
    # RETURN RESPONSE
    # =========================================================

    return {

        "kpis": {

            "total_revenue": float(
                total_revenue
            ),

            "total_sales": int(
                total_sales
            ),

            "total_customers": int(
                total_customers
            ),

            "average_order_value": round(
                float(average_order_value),
                2
            ),

            "total_quantity": int(
                total_quantity
            )
        },


        "customers": {

            "total_customers": int(
                total_customers
            ),

            "active_customers": int(
                active_customers
            ),

            "inactive_customers": int(
                inactive_customers
            ),

            "new_customers": int(
                new_customers
            )
        },


        "sales": {

            "today": float(
                today_revenue or 0
            ),

            "this_week": float(
                week_revenue or 0
            ),

            "this_month": float(
                month_revenue or 0
            )
        }
    }