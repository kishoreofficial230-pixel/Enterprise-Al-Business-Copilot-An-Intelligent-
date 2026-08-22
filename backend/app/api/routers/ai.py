from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.core.security import get_current_user

from app.models.sales import Sale
from app.models.customer import Customer

from app.api.routers.forecast import sales_forecast


router = APIRouter(
    prefix="/ai",
    tags=["AI Copilot"],
)


# =====================================================
# REQUEST MODEL
# =====================================================

class ChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )


# =====================================================
# MONEY FORMATTER
# =====================================================

def money(value):

    return (
        f"₹{float(value or 0):,.2f}"
    )


# =====================================================
# BUILD BUSINESS ANSWER
# =====================================================

def build_business_answer(
    question: str,
    db: Session,
    current_user: dict
) -> str:

    q = (
        question
        .lower()
        .strip()
    )


    # =====================================================
    # BASIC BUSINESS KPI
    # =====================================================

    total_revenue = float(

        db.query(
            func.coalesce(
                func.sum(
                    Sale.amount
                ),
                0
            )
        ).scalar()

        or 0
    )


    total_sales = (
        db.query(
            Sale
        )
        .count()
    )


    total_quantity = int(

        db.query(
            func.coalesce(
                func.sum(
                    Sale.quantity
                ),
                0
            )
        ).scalar()

        or 0
    )


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


    average_order = (

        total_revenue /
        total_sales

        if total_sales

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


    # =====================================================
    # LOWEST PRODUCT
    # =====================================================

    lowest_product = (

        db.query(

            Sale.product_name,

            func.sum(
                Sale.amount
            ).label(
                "revenue"
            ),
        )

        .group_by(
            Sale.product_name
        )

        .order_by(
            func.sum(
                Sale.amount
            ).asc()
        )

        .first()
    )


    # =====================================================
    # TOP CATEGORY
    # =====================================================

    top_category = (

        db.query(

            Sale.category,

            func.sum(
                Sale.amount
            ).label(
                "revenue"
            ),
        )

        .filter(
            Sale.category.isnot(
                None
            )
        )

        .group_by(
            Sale.category
        )

        .order_by(
            func.sum(
                Sale.amount
            ).desc()
        )

        .first()
    )


    # =====================================================
    # RECENT SALES
    # =====================================================

    recent_sales = (

        db.query(
            Sale
        )

        .order_by(
            Sale.sale_date.desc()
        )

        .limit(
            5
        )

        .all()
    )


    # =====================================================
    # MACHINE LEARNING FORECAST QUESTIONS
    # IMPORTANT:
    # THIS MUST COME BEFORE NORMAL SALES / REVENUE CHECKS
    # =====================================================

    forecast_keywords = [

        "forecast",

        "prediction",

        "predict",

        "next 7 days",

        "next seven days",

        "future sales",

        "future revenue",

        "next week revenue",

        "next week sales",

        "ml forecast",

        "machine learning forecast",

        "sales prediction",

        "revenue prediction",
    ]


    if any(
        keyword in q
        for keyword in forecast_keywords
    ):

        forecast_result = (
            sales_forecast(
                db=db,
                current_user=current_user
            )
        )


        forecast_rows = (
            forecast_result.get(
                "forecast",
                []
            )
        )


        forecast_summary = (
            forecast_result.get(
                "summary",
                {}
            )
        )


        model_info = (
            forecast_result.get(
                "model_info",
                {}
            )
        )


        insight = (
            forecast_result.get(
                "insight",
                ""
            )
        )


        # =================================================
        # NO FORECAST DATA
        # =================================================

        if not forecast_rows:

            return (
                "I cannot generate a sales forecast yet. "
                "More historical sales data is required."
            )


        method = (
            model_info.get(
                "method",
                "Unknown"
            )
        )


        ml_ready = (
            model_info.get(
                "ml_ready",
                False
            )
        )


        training_days = (
            model_info.get(
                "training_days",
                0
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
                "N/A"
            )
        )


        trend_per_day = float(
            model_info.get(
                "revenue_trend_per_day",
                0
            )
            or 0
        )


        forecast_start = (
            model_info.get(
                "forecast_start_date",
                "N/A"
            )
        )


        forecast_end = (
            model_info.get(
                "forecast_end_date",
                "N/A"
            )
        )


        forecast_7_days = float(
            forecast_summary.get(
                "forecast_7_days",
                0
            )
            or 0
        )


        predicted_daily_average = float(
            forecast_summary.get(
                "predicted_average_daily_revenue",
                0
            )
            or 0
        )


        predicted_total_orders = int(
            forecast_summary.get(
                "predicted_total_orders",
                0
            )
            or 0
        )


        predicted_total_quantity = int(
            forecast_summary.get(
                "predicted_total_quantity",
                0
            )
            or 0
        )


        # =================================================
        # R2 DISPLAY
        # =================================================

        if r2_score is not None:

            r2_text = (
                f"{float(r2_score):.3f}"
            )

        else:

            r2_text = (
                "N/A"
            )


        # =================================================
        # DAILY FORECAST LINES
        # =================================================

        daily_lines = []


        for item in forecast_rows:

            daily_lines.append(

                f"• {item.get('date', 'N/A')} — "
                f"Revenue: "
                f"{money(item.get('predicted_revenue', 0))}, "
                f"Orders: "
                f"{int(item.get('predicted_orders', 0))}, "
                f"Quantity: "
                f"{int(item.get('predicted_quantity', 0))}"
            )


        # =================================================
        # ML ACTIVE RESPONSE
        # =================================================

        if ml_ready:

            return (

                "🔮 Machine Learning Sales Forecast\n\n"

                f"Model: {method}\n"

                f"ML Status: Active\n"

                f"Training Days: {training_days}\n"

                f"Model Quality: {model_quality}\n"

                f"R² Score: {r2_text}\n"

                f"Revenue Trend: {trend_direction}\n"

                f"Revenue Trend / Day: "
                f"{money(trend_per_day)}\n\n"

                f"Forecast Period: "
                f"{forecast_start} to "
                f"{forecast_end}\n\n"

                f"Predicted 7-Day Revenue: "
                f"{money(forecast_7_days)}\n"

                f"Predicted Average Daily Revenue: "
                f"{money(predicted_daily_average)}\n"

                f"Predicted Total Orders: "
                f"{predicted_total_orders}\n"

                f"Predicted Total Quantity: "
                f"{predicted_total_quantity}\n\n"

                "Daily Forecast:\n"

                + "\n".join(
                    daily_lines
                )

                + "\n\n"

                + (
                    insight
                    if insight
                    else
                    "Machine Learning forecast generated successfully."
                )
            )


        # =================================================
        # FALLBACK RESPONSE
        # =================================================

        return (

            "🔮 Sales Forecast\n\n"

            f"Forecast Method: "
            f"{method}\n"

            f"ML Status: Not Active Yet\n"

            f"Training Days: "
            f"{training_days}\n\n"

            f"Predicted 7-Day Revenue: "
            f"{money(forecast_7_days)}\n\n"

            "Daily Forecast:\n"

            + "\n".join(
                daily_lines
            )

            + "\n\n"

            + (
                insight
                if insight
                else
                "More historical data is required to activate Machine Learning."
            )
        )


    # =====================================================
    # BUSINESS RECOMMENDATION
    # =====================================================

    recommendation_keywords = [

        "recommend",

        "recommendation",

        "improve",

        "what should i do",

        "what should i do next",

        "increase revenue",

        "grow revenue",

        "business advice",

        "decision",

        "strategy",
    ]


    if any(
        keyword in q
        for keyword in recommendation_keywords
    ):

        recommendations = []


        if top_product:

            recommendations.append(

                f"1. Focus more on "
                f"'{top_product.product_name}'. "
                f"It is currently your strongest product "
                f"with {money(top_product.revenue)} "
                f"in revenue."
            )


        if top_category:

            recommendations.append(

                f"2. Your strongest category is "
                f"'{top_category.category}' "
                f"with {money(top_category.revenue)}. "
                f"Consider expanding products "
                f"in this category."
            )


        if active_customers > 0:

            recommendations.append(

                f"3. You currently have "
                f"{active_customers} active customers. "
                f"Use repeat-purchase offers, "
                f"loyalty programs and cross-selling."
            )


        if inactive_customers > 0:

            recommendations.append(

                f"4. You have "
                f"{inactive_customers} inactive customers. "
                f"Run a re-engagement campaign "
                f"to bring them back."
            )


        if (
            lowest_product
            and
            top_product
            and
            lowest_product.product_name
            !=
            top_product.product_name
        ):

            recommendations.append(

                f"5. Review "
                f"'{lowest_product.product_name}'. "
                f"It currently has only "
                f"{money(lowest_product.revenue)} "
                f"in revenue."
            )


        recommendations.append(

            f"6. Your current average order value is "
            f"{money(average_order)}. "
            f"Use bundles, upselling and cross-selling "
            f"to increase order value."
        )


        return (

            "📊 Business Decision Support\n\n"

            f"Current Revenue: "
            f"{money(total_revenue)}\n"

            f"Total Sales: "
            f"{total_sales}\n"

            f"Customers: "
            f"{total_customers}\n\n"

            "Recommended Actions:\n"

            + "\n".join(
                recommendations
            )
        )


    # =====================================================
    # STRENGTHS AND WEAKNESSES
    # =====================================================

    if (
        "strength" in q
        or
        "weakness" in q
        or
        "swot" in q
    ):

        strengths = []

        weaknesses = []


        if top_product:

            strengths.append(

                f"• Strongest Product: "
                f"{top_product.product_name} "
                f"({money(top_product.revenue)} revenue)"
            )


        if top_category:

            strengths.append(

                f"• Strongest Category: "
                f"{top_category.category} "
                f"({money(top_category.revenue)} revenue)"
            )


        if active_customers > 0:

            strengths.append(

                f"• Active Customer Base: "
                f"{active_customers} customers"
            )


        if inactive_customers > 0:

            weaknesses.append(

                f"• {inactive_customers} inactive customers "
                f"require re-engagement"
            )


        if lowest_product:

            weaknesses.append(

                f"• Lowest Performing Product: "
                f"{lowest_product.product_name} "
                f"({money(lowest_product.revenue)} revenue)"
            )


        if not strengths:

            strengths.append(
                "• More business data is required."
            )


        if not weaknesses:

            weaknesses.append(
                "• No major weakness detected from current data."
            )


        return (

            "💡 Business Strengths & Weaknesses\n\n"

            "Strengths:\n"

            + "\n".join(
                strengths
            )

            + "\n\n"

            "Weaknesses:\n"

            + "\n".join(
                weaknesses
            )
        )


    # =====================================================
    # PRODUCT FOCUS
    # =====================================================

    if (
        "focus product" in q
        or
        "product should i focus" in q
        or
        "which product should" in q
    ):

        if top_product:

            return (

                f"You should currently focus on "
                f"'{top_product.product_name}'. "
                f"It is generating the highest revenue "
                f"at {money(top_product.revenue)}. "
                f"Consider increasing stock, promotions "
                f"and cross-selling around this product."
            )


        return (
            "There are no sales records yet, "
            "so I cannot recommend a product."
        )


    # =====================================================
    # TOP PRODUCT
    # =====================================================

    if any(
        keyword in q

        for keyword in [

            "best product",

            "top product",

            "highest product",

            "best selling",

            "highest sales product",
        ]
    ):

        if top_product:

            return (

                f"Your top product by revenue is "
                f"'{top_product.product_name}' "
                f"with {money(top_product.revenue)} "
                f"in revenue and "
                f"{int(top_product.quantity or 0)} "
                f"units sold."
            )


        return (
            "There are no sales records yet."
        )


    # =====================================================
    # CATEGORY
    # =====================================================

    if "category" in q:

        if top_category:

            return (

                f"Your strongest category by revenue is "
                f"'{top_category.category}' "
                f"with {money(top_category.revenue)}."
            )


        return (
            "There are no categorized sales records yet."
        )


    # =====================================================
    # RECENT SALES
    # =====================================================

    if any(
        keyword in q

        for keyword in [

            "recent",

            "latest",

            "last sale",
        ]
    ):

        if not recent_sales:

            return (
                "There are no sales records yet."
            )


        lines = [
            "Here are the latest sales:"
        ]


        for sale in recent_sales:

            date_text = (

                sale.sale_date.strftime(
                    "%d/%m/%Y"
                )

                if sale.sale_date

                else "N/A"
            )


            lines.append(

                f"• {sale.product_name} — "
                f"{money(sale.amount)} — "
                f"{sale.customer_name or 'Unknown Customer'} — "
                f"{date_text}"
            )


        return "\n".join(
            lines
        )


    # =====================================================
    # AVERAGE ORDER VALUE
    # =====================================================

    if (
        "average order value" in q
        or
        "average sale" in q
        or
        "aov" in q
        or
        "average" in q
    ):

        return (

            f"Your average order value is "
            f"{money(average_order)}. "
            f"You currently have "
            f"{total_sales} sales generating "
            f"{money(total_revenue)} "
            f"in total revenue."
        )


    # =====================================================
    # QUANTITY
    # =====================================================

    if (
        "quantity" in q
        or
        "units" in q
    ):

        return (

            f"The total quantity sold is "
            f"{total_quantity} units "
            f"across {total_sales} sales."
        )


    # =====================================================
    # CUSTOMER INFORMATION
    # =====================================================

    if (
        "customer" in q
        or
        "client" in q
    ):

        return (

            f"You currently have "
            f"{total_customers} customers: "
            f"{active_customers} active "
            f"and {inactive_customers} inactive."
        )


    # =====================================================
    # SALES INFORMATION
    # =====================================================

    if any(
        keyword in q

        for keyword in [

            "sales",

            "orders",

            "order count",
        ]
    ):

        return (

            f"You currently have "
            f"{total_sales} sales/orders. "
            f"The total quantity sold is "
            f"{total_quantity} units "
            f"and total revenue is "
            f"{money(total_revenue)}."
        )


    # =====================================================
    # REVENUE INFORMATION
    # =====================================================

    if any(
        keyword in q

        for keyword in [

            "revenue",

            "income",

            "turnover",
        ]
    ):

        return (

            f"Your total business revenue is "
            f"{money(total_revenue)}. "
            f"You have {total_sales} sales "
            f"with an average order value of "
            f"{money(average_order)}."
        )


    # =====================================================
    # DEFAULT BUSINESS SUMMARY
    # =====================================================

    return (

        "📊 Current Business Summary\n\n"

        f"• Revenue: "
        f"{money(total_revenue)}\n"

        f"• Sales / Orders: "
        f"{total_sales}\n"

        f"• Quantity Sold: "
        f"{total_quantity}\n"

        f"• Customers: "
        f"{total_customers}\n"

        f"• Active Customers: "
        f"{active_customers}\n"

        f"• Inactive Customers: "
        f"{inactive_customers}\n"

        f"• Average Order Value: "
        f"{money(average_order)}\n"

        f"• Top Product: "
        f"{top_product.product_name if top_product else 'N/A'}\n"

        f"• Top Category: "
        f"{top_category.category if top_category else 'N/A'}"
    )


# =====================================================
# AI CHAT ENDPOINT
# =====================================================

@router.post("/chat")
def ai_chat(
    request: ChatRequest,
    db: Session = Depends(
        get_db
    ),
    current_user: dict = Depends(
        get_current_user
    ),
):

    # =====================================================
    # VALIDATE MESSAGE
    # =====================================================

    if not request.message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )


    # =====================================================
    # BUILD ANSWER
    # =====================================================

    answer = build_business_answer(
        question=request.message,
        db=db,
        current_user=current_user
    )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "message":
            request.message,

        "answer":
            answer,

        "user_id":
            current_user.get(
                "sub"
            ),
    }