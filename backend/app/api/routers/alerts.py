from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from sqlalchemy import func

from datetime import datetime

from app.database.database import get_db
from app.core.security import get_current_user

from app.models.sales import Sale
from app.models.customer import Customer

from app.api.routers.forecast import sales_forecast


router = APIRouter(
    prefix="/alerts",
    tags=["AI Business Alerts"],
)


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def safe_float(value):

    try:
        return float(
            value or 0
        )

    except (
        TypeError,
        ValueError
    ):
        return 0.0


def safe_int(value):

    try:
        return int(
            value or 0
        )

    except (
        TypeError,
        ValueError
    ):
        return 0


def money(value):

    return (
        f"₹{safe_float(value):,.2f}"
    )


# =====================================================
# BUSINESS ALERTS
# =====================================================

@router.get("/business")
def business_alerts(
    db: Session = Depends(
        get_db
    ),
    current_user: dict = Depends(
        get_current_user
    ),
):

    alerts = []


    # =====================================================
    # BASIC SALES DATA
    # =====================================================

    total_revenue = safe_float(

        db.query(
            func.coalesce(
                func.sum(
                    Sale.amount
                ),
                0
            )
        ).scalar()
    )


    total_sales = (

        db.query(
            Sale
        )
        .count()
    )


    total_quantity = safe_int(

        db.query(
            func.coalesce(
                func.sum(
                    Sale.quantity
                ),
                0
            )
        ).scalar()
    )


    # =====================================================
    # CUSTOMER DATA
    # =====================================================

    total_customers = (

        db.query(
            Customer
        )
        .count()
    )


    active_customers = (

        db.query(
            Customer
        )
        .filter(
            Customer.status ==
            "Active"
        )
        .count()
    )


    inactive_customers = (

        db.query(
            Customer
        )
        .filter(
            Customer.status ==
            "Inactive"
        )
        .count()
    )


    inactive_percentage = (

        (
            inactive_customers /
            total_customers
        ) * 100

        if total_customers > 0

        else 0
    )


    # =====================================================
    # AVERAGE ORDER VALUE
    # =====================================================

    average_order_value = (

        total_revenue /
        total_sales

        if total_sales > 0

        else 0
    )


    # =====================================================
    # TOP PRODUCT
    # =====================================================

    top_product = (

        db.query(

            Sale.product_name,

            func.sum(
                Sale.amount
            ).label(
                "revenue"
            ),

            func.sum(
                Sale.quantity
            ).label(
                "quantity"
            ),
        )

        .group_by(
            Sale.product_name
        )

        .order_by(
            func.sum(
                Sale.amount
            ).desc()
        )

        .first()
    )


    top_product_revenue = (

        safe_float(
            top_product.revenue
        )

        if top_product

        else 0
    )


    top_product_percentage = (

        (
            top_product_revenue /
            total_revenue
        ) * 100

        if total_revenue > 0

        else 0
    )


    # =====================================================
    # FORECAST DATA
    # =====================================================

    forecast_data = sales_forecast(
        db=db,
        current_user=current_user
    )


    forecast_summary = (
        forecast_data.get(
            "summary",
            {}
        )
    )


    model_info = (
        forecast_data.get(
            "model_info",
            {}
        )
    )


    forecast_7_days = safe_float(
        forecast_summary.get(
            "forecast_7_days",
            0
        )
    )


    average_daily_revenue = safe_float(
        forecast_summary.get(
            "average_daily_revenue",
            0
        )
    )


    expected_normal_7_days = (
        average_daily_revenue * 7
    )


    ml_ready = (
        model_info.get(
            "ml_ready",
            False
        )
    )


    model_method = (
        model_info.get(
            "method",
            "Unknown"
        )
    )


    model_quality = (
        model_info.get(
            "model_quality",
            "Not Available"
        )
    )


    r2_score = (
        model_info.get(
            "revenue_r2_score"
        )
    )


    trend_direction = (
        model_info.get(
            "trend_direction",
            "Unknown"
        )
    )


    revenue_trend_per_day = safe_float(
        model_info.get(
            "revenue_trend_per_day",
            0
        )
    )


    # =====================================================
    # RISK 1
    # NO SALES
    # =====================================================

    if total_sales == 0:

        alerts.append({

            "type":
                "RISK",

            "severity":
                "HIGH",

            "title":
                "No Sales Activity",

            "message":
                "No sales transactions are available "
                "in the system.",

            "recommendation":
                "Add sales data and monitor business "
                "performance regularly.",
        })


    # =====================================================
    # RISK 2
    # NO CUSTOMERS
    # =====================================================

    if total_customers == 0:

        alerts.append({

            "type":
                "RISK",

            "severity":
                "HIGH",

            "title":
                "No Customer Data",

            "message":
                "No customer records are currently "
                "available.",

            "recommendation":
                "Add customer records before performing "
                "customer behaviour analysis.",
        })


    # =====================================================
    # RISK 3
    # INACTIVE CUSTOMERS
    # =====================================================

    if inactive_percentage >= 50:

        alerts.append({

            "type":
                "RISK",

            "severity":
                "HIGH",

            "title":
                "High Customer Inactivity",

            "message":
                f"{inactive_percentage:.1f}% of customers "
                f"are currently inactive.",

            "recommendation":
                "Launch a customer re-engagement campaign "
                "with personalised offers and follow-ups.",
        })


    elif inactive_percentage >= 20:

        alerts.append({

            "type":
                "RISK",

            "severity":
                "MEDIUM",

            "title":
                "Customer Inactivity Detected",

            "message":
                f"{inactive_customers} out of "
                f"{total_customers} customers "
                f"are inactive "
                f"({inactive_percentage:.1f}%).",

            "recommendation":
                "Contact inactive customers and use "
                "discounts or loyalty offers to improve "
                "retention.",
        })


    elif (
        total_customers > 0
        and
        inactive_customers == 0
    ):

        alerts.append({

            "type":
                "OPPORTUNITY",

            "severity":
                "LOW",

            "title":
                "Strong Customer Activity",

            "message":
                "All customers are currently active.",

            "recommendation":
                "Maintain engagement through loyalty "
                "programs and personalised offers.",
        })


    # =====================================================
    # RISK 4
    # PRODUCT DEPENDENCY
    # =====================================================

    if (
        top_product
        and
        top_product_percentage >= 60
    ):

        alerts.append({

            "type":
                "RISK",

            "severity":
                "HIGH",

            "title":
                "High Product Dependency",

            "message":
                f"{top_product.product_name} contributes "
                f"{top_product_percentage:.1f}% of total "
                f"business revenue.",

            "recommendation":
                "Diversify revenue by promoting other "
                "products and categories.",
        })


    elif (
        top_product
        and
        top_product_percentage >= 40
    ):

        alerts.append({

            "type":
                "RISK",

            "severity":
                "MEDIUM",

            "title":
                "Product Revenue Concentration",

            "message":
                f"{top_product.product_name} contributes "
                f"{top_product_percentage:.1f}% of total "
                f"revenue.",

            "recommendation":
                "Continue supporting the top product, "
                "but increase sales from other products "
                "to reduce dependency.",
        })


    elif top_product:

        alerts.append({

            "type":
                "OPPORTUNITY",

            "severity":
                "LOW",

            "title":
                "Top Product Opportunity",

            "message":
                f"{top_product.product_name} is currently "
                f"the strongest product with "
                f"{money(top_product_revenue)} revenue.",

            "recommendation":
                "Use targeted promotions, bundles and "
                "cross-selling around this product.",
        })


    # =====================================================
    # RISK 5
    # ML NOT READY
    # =====================================================

    if not ml_ready:

        training_days = safe_int(
            model_info.get(
                "training_days",
                0
            )
        )


        minimum_days = safe_int(
            model_info.get(
                "minimum_ml_days",
                5
            )
        )


        alerts.append({

            "type":
                "RISK",

            "severity":
                "MEDIUM",

            "title":
                "Machine Learning Model Not Ready",

            "message":
                f"Only {training_days} historical "
                f"sales days are available. "
                f"{minimum_days} are required.",

            "recommendation":
                "Add more dated historical sales records "
                "to activate the Machine Learning model.",
        })


    # =====================================================
    # ML MODEL QUALITY
    # =====================================================

    if (
        ml_ready
        and
        r2_score is not None
    ):

        r2_value = safe_float(
            r2_score
        )


        if r2_value < 0.30:

            alerts.append({

                "type":
                    "RISK",

                "severity":
                    "HIGH",

                "title":
                    "Weak Forecast Model",

                "message":
                    f"The forecast model R² score is "
                    f"{r2_value:.3f}, indicating weak "
                    f"historical fit.",

                "recommendation":
                    "Add more historical sales data and "
                    "improve the forecasting model before "
                    "using predictions for major decisions.",
            })


        elif r2_value < 0.50:

            alerts.append({

                "type":
                    "RISK",

                "severity":
                    "MEDIUM",

                "title":
                    "Forecast Model Needs Improvement",

                "message":
                    f"The forecast model R² score is "
                    f"{r2_value:.3f}.",

                "recommendation":
                    "Collect more historical data to "
                    "improve prediction reliability.",
            })


        else:

            alerts.append({

                "type":
                    "INFO",

                "severity":
                    "LOW",

                "title":
                    "Machine Learning Forecast Active",

                "message":
                    f"{model_method} is active with "
                    f"{model_quality} model quality "
                    f"and R² score "
                    f"{r2_value:.3f}.",

                "recommendation":
                    "Continue collecting sales history "
                    "to improve model reliability.",
            })


    # =====================================================
    # RISK 6
    # REVENUE TREND
    # =====================================================

    if trend_direction == "Decreasing":

        alerts.append({

            "type":
                "RISK",

            "severity":
                "HIGH",

            "title":
                "Revenue Decline Detected",

            "message":
                f"Machine Learning detected a decreasing "
                f"revenue trend of approximately "
                f"{money(abs(revenue_trend_per_day))} "
                f"per day.",

            "recommendation":
                "Review low-performing products, pricing, "
                "marketing and customer retention "
                "strategies immediately.",
        })


    elif trend_direction == "Increasing":

        alerts.append({

            "type":
                "OPPORTUNITY",

            "severity":
                "LOW",

            "title":
                "Revenue Growth Trend",

            "message":
                f"Revenue is trending upward by "
                f"approximately "
                f"{money(revenue_trend_per_day)} "
                f"per day.",

            "recommendation":
                "Maintain inventory and marketing "
                "capacity to support expected growth.",
        })


    # =====================================================
    # FORECAST GROWTH ANALYSIS
    # =====================================================

    forecast_growth_percentage = 0


    if expected_normal_7_days > 0:

        forecast_growth_percentage = (

            (
                forecast_7_days -
                expected_normal_7_days
            )
            /
            expected_normal_7_days
        ) * 100


    if forecast_growth_percentage >= 20:

        alerts.append({

            "type":
                "OPPORTUNITY",

            "severity":
                "LOW",

            "title":
                "Strong Revenue Growth Opportunity",

            "message":
                f"The next 7-day ML forecast is "
                f"{money(forecast_7_days)}, which is "
                f"approximately "
                f"{forecast_growth_percentage:.1f}% "
                f"above the historical daily average "
                f"projection.",

            "recommendation":
                "Prepare stock, sales capacity and "
                "marketing campaigns for higher demand.",
        })


    elif forecast_growth_percentage <= -20:

        alerts.append({

            "type":
                "RISK",

            "severity":
                "HIGH",

            "title":
                "Forecast Revenue Risk",

            "message":
                f"Forecast revenue is approximately "
                f"{abs(forecast_growth_percentage):.1f}% "
                f"below the historical average projection.",

            "recommendation":
                "Review marketing, product demand and "
                "customer engagement before revenue "
                "declines further.",
        })


    # =====================================================
    # AVERAGE ORDER VALUE INFORMATION
    # =====================================================

    if total_sales > 0:

        alerts.append({

            "type":
                "INFO",

            "severity":
                "LOW",

            "title":
                "Average Order Value",

            "message":
                f"Current average order value is "
                f"{money(average_order_value)}.",

            "recommendation":
                "Use product bundles, upselling and "
                "cross-selling to improve order value.",
        })


    # =====================================================
    # COUNT ALERT LEVELS
    # =====================================================

    high_risk_count = sum(

        1

        for alert
        in alerts

        if alert[
            "severity"
        ] == "HIGH"
    )


    medium_risk_count = sum(

        1

        for alert
        in alerts

        if alert[
            "severity"
        ] == "MEDIUM"
    )


    low_risk_count = sum(

        1

        for alert
        in alerts

        if alert[
            "severity"
        ] == "LOW"
    )


    # =====================================================
    # OVERALL RISK LEVEL
    # =====================================================

    if high_risk_count > 0:

        overall_risk_level = (
            "HIGH"
        )


    elif medium_risk_count > 0:

        overall_risk_level = (
            "MEDIUM"
        )


    else:

        overall_risk_level = (
            "LOW"
        )


    # =====================================================
    # BUSINESS HEALTH SCORE
    # =====================================================

    health_score = 100


    health_score -= (
        high_risk_count * 20
    )


    health_score -= (
        medium_risk_count * 10
    )


    health_score = max(
        health_score,
        0
    )


    if health_score >= 80:

        health_status = (
            "Healthy"
        )


    elif health_score >= 60:

        health_status = (
            "Needs Attention"
        )


    else:

        health_status = (
            "High Risk"
        )


    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "business_health": {

            "score":
                health_score,

            "status":
                health_status,

            "overall_risk_level":
                overall_risk_level,
        },

        "alert_summary": {

            "total_alerts":
                len(
                    alerts
                ),

            "high":
                high_risk_count,

            "medium":
                medium_risk_count,

            "low":
                low_risk_count,
        },

        "business_metrics": {

            "total_revenue":
                round(
                    total_revenue,
                    2
                ),

            "total_sales":
                total_sales,

            "total_quantity":
                total_quantity,

            "total_customers":
                total_customers,

            "active_customers":
                active_customers,

            "inactive_customers":
                inactive_customers,

            "inactive_customer_percentage":
                round(
                    inactive_percentage,
                    2
                ),

            "average_order_value":
                round(
                    average_order_value,
                    2
                ),

            "top_product":
                (
                    top_product.product_name
                    if top_product
                    else None
                ),

            "top_product_revenue_percentage":
                round(
                    top_product_percentage,
                    2
                ),
        },

        "forecast_metrics": {

            "ml_ready":
                ml_ready,

            "method":
                model_method,

            "model_quality":
                model_quality,

            "r2_score":
                r2_score,

            "trend_direction":
                trend_direction,

            "revenue_trend_per_day":
                round(
                    revenue_trend_per_day,
                    2
                ),

            "forecast_7_days":
                round(
                    forecast_7_days,
                    2
                ),

            "forecast_growth_percentage":
                round(
                    forecast_growth_percentage,
                    2
                ),
        },

        "alerts":
            alerts,

        "generated_at":
            datetime.now().isoformat(),

        "user_id":
            current_user.get(
                "sub"
            ),
    }