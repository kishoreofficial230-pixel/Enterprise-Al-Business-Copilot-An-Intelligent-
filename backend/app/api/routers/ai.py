from datetime import date, datetime, timedelta, time
import calendar
import os
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session


# =====================================================
# OPTIONAL .ENV LOADING
# =====================================================

try:
    from dotenv import load_dotenv

    load_dotenv()

except ImportError:
    pass


# =====================================================
# OPTIONAL GEMINI AI
# =====================================================

try:
    from google import genai

except ImportError:
    genai = None


# =====================================================
# PROJECT IMPORTS
# =====================================================

from app.database.database import get_db
from app.core.security import get_current_user

from app.models.sales import Sale
from app.models.customer import Customer
from app.models.user import User

from app.api.routers.forecast import sales_forecast


# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI Copilot"],
)


# =====================================================
# REQUEST SCHEMA
# =====================================================

class ChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
    )


# =====================================================
# SETTINGS
# =====================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


BUSINESS_WORDS = {

    "sale",
    "sales",

    "order",
    "orders",

    "revenue",
    "income",
    "turnover",

    "amount",

    "quantity",
    "units",
    "sold",

    "business",

    "product",
    "products",

    "category",

    "customer",
    "customers",

    "forecast",
    "predict",
    "prediction",
}


MONTH_PATTERN = (

    r"jan(?:uary)?|"
    r"feb(?:ruary)?|"
    r"mar(?:ch)?|"
    r"apr(?:il)?|"
    r"may|"
    r"jun(?:e)?|"
    r"jul(?:y)?|"
    r"aug(?:ust)?|"
    r"sep(?:tember)?|"
    r"oct(?:ober)?|"
    r"nov(?:ember)?|"
    r"dec(?:ember)?"
)


# =====================================================
# BASIC HELPERS
# =====================================================

def money(value):

    return (
        f"₹{float(value or 0):,.2f}"
    )


def normalize_text(
    value: str,
):

    return " ".join(
        str(
            value or ""
        )
        .lower()
        .strip()
        .split()
    )


def contains_any(
    text: str,
    phrases,
):

    return any(
        phrase in text
        for phrase in phrases
    )


def has_business_word(
    text: str,
):

    return any(

        re.search(
            rf"\b{re.escape(word)}\b",
            text,
            flags=re.IGNORECASE,
        )

        for word
        in BUSINESS_WORDS
    )


def format_date(
    value: date,
):

    return value.strftime(
        "%d %B %Y"
    )


def safe_float(
    value,
):

    try:

        return float(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


def safe_int(
    value,
):

    try:

        return int(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0


# =====================================================
# LOGGED-IN USER
# =====================================================

def get_logged_in_user(
    db: Session,
    current_user: dict,
):

    user_id = current_user.get(
        "sub"
    )


    if user_id is not None:

        try:

            user = (

                db.query(
                    User
                )

                .filter(
                    User.id ==
                    int(
                        user_id
                    )
                )

                .first()
            )


            if user:

                return user


        except (
            TypeError,
            ValueError,
        ):

            pass


    email = current_user.get(
        "email"
    )


    if email:

        return (

            db.query(
                User
            )

            .filter(
                User.email ==
                email
            )

            .first()
        )


    return None


def get_user_details(
    db: Session,
    current_user: dict,
):

    user = get_logged_in_user(
        db,
        current_user,
    )


    if user:

        return {

            "full_name":
                user.full_name,

            "email":
                user.email,

            "role":
                user.role,
        }


    email = current_user.get(
        "email",
        "Unknown",
    )


    role = current_user.get(
        "role",
        "Employee",
    )


    if email != "Unknown":

        full_name = (

            email
            .split("@")[0]
            .replace(
                ".",
                " ",
            )
            .replace(
                "_",
                " ",
            )
            .title()
        )

    else:

        full_name = "User"


    return {

        "full_name":
            full_name,

        "email":
            email,

        "role":
            role,
    }


# =====================================================
# BUSINESS METRICS
# =====================================================

def get_business_metrics(
    db: Session,
):

    total_revenue = safe_float(

        db.query(

            func.coalesce(

                func.sum(
                    Sale.amount
                ),

                0,
            )
        )

        .scalar()
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

                0,
            )
        )

        .scalar()
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

            func.lower(
                Customer.status
            )
            ==
            "active"
        )

        .count()
    )


    inactive_customers = (

        db.query(
            Customer
        )

        .filter(

            func.lower(
                Customer.status
            )
            ==
            "inactive"
        )

        .count()
    )


    average_order = (

        total_revenue /
        total_sales

        if total_sales

        else 0
    )


    # =================================================
    # TOP PRODUCT
    # =================================================

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

            func.count(
                Sale.id
            ).label(
                "orders"
            ),
        )

        .filter(
            Sale.product_name
            .isnot(None)
        )

        .group_by(
            Sale.product_name
        )

        .order_by(

            func.sum(
                Sale.amount
            )
            .desc()
        )

        .first()
    )


    # =================================================
    # TOP CATEGORY
    # =================================================

    top_category = (

        db.query(

            Sale.category,

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

            func.count(
                Sale.id
            ).label(
                "orders"
            ),
        )

        .filter(
            Sale.category
            .isnot(None)
        )

        .group_by(
            Sale.category
        )

        .order_by(

            func.sum(
                Sale.amount
            )
            .desc()
        )

        .first()
    )


    return {

        "total_revenue":
            total_revenue,

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

        "average_order":
            average_order,

        "top_product":
            top_product,

        "top_category":
            top_category,
    }


# =====================================================
# DATE HELPERS
# =====================================================

def clean_date_text(
    value: str,
):

    value = re.sub(

        r"(\d)(st|nd|rd|th)\b",

        r"\1",

        value,

        flags=re.IGNORECASE,
    )


    value = value.replace(
        ",",
        " ",
    )


    return " ".join(
        value.split()
    )


def parse_date_text(
    value: str,
):

    cleaned = clean_date_text(
        value
    )


    formats = [

        "%Y-%m-%d",

        "%d/%m/%Y",

        "%d-%m-%Y",

        "%d %B %Y",

        "%d %b %Y",

        "%B %d %Y",

        "%b %d %Y",
    ]


    for date_format in formats:

        try:

            return datetime.strptime(

                cleaned,

                date_format,

            ).date()


        except ValueError:

            pass


    return None


def extract_explicit_dates(
    text: str,
):

    patterns = [

        r"\b\d{4}-\d{1,2}-\d{1,2}\b",

        r"\b\d{1,2}/\d{1,2}/\d{4}\b",

        r"\b\d{1,2}-\d{1,2}-\d{4}\b",

        (
            rf"\b\d{{1,2}}"
            rf"(?:st|nd|rd|th)?"
            rf"\s+"
            rf"(?:{MONTH_PATTERN})"
            rf"\s+\d{{4}}\b"
        ),

        (
            rf"\b(?:{MONTH_PATTERN})"
            rf"\s+\d{{1,2}}"
            rf"(?:st|nd|rd|th)?"
            rf"(?:,)?"
            rf"\s+\d{{4}}\b"
        ),
    ]


    found = []


    for pattern in patterns:

        for match in re.finditer(

            pattern,

            text,

            flags=re.IGNORECASE,
        ):

            parsed = parse_date_text(
                match.group(0)
            )


            if parsed:

                found.append(

                    (
                        match.start(),
                        parsed,
                    )
                )


    found.sort(

        key=lambda item:
            item[0]
    )


    unique_dates = []


    for _, parsed_date in found:

        if (
            parsed_date
            not in
            unique_dates
        ):

            unique_dates.append(
                parsed_date
            )


    return unique_dates


def extract_month_period(
    text: str,
):

    match = re.search(

        rf"\b({MONTH_PATTERN})"
        rf"\s+"
        rf"(\d{{4}})\b",

        text,

        flags=re.IGNORECASE,
    )


    if not match:

        return None


    month_text = (
        match.group(1)
    )


    year = int(
        match.group(2)
    )


    month_number = None


    for format_string in (
        "%B",
        "%b",
    ):

        try:

            month_number = (

                datetime.strptime(

                    month_text,

                    format_string,

                ).month
            )


            break


        except ValueError:

            pass


    if not month_number:

        return None


    last_day = (

        calendar.monthrange(

            year,

            month_number,

        )[1]
    )


    start_date = date(

        year,

        month_number,

        1,
    )


    end_date = date(

        year,

        month_number,

        last_day,
    )


    label = datetime(

        year,

        month_number,

        1,

    ).strftime(
        "%B %Y"
    )


    return (

        start_date,

        end_date,

        label,
    )


def get_relative_period(
    question: str,
):

    today = date.today()


    # =================================================
    # YESTERDAY
    # =================================================

    if re.search(

        r"\byesterday\b",

        question,
    ):

        target = (

            today -

            timedelta(
                days=1
            )
        )


        return (

            target,

            target,

            "Yesterday",
        )


    # =================================================
    # TODAY
    # =================================================

    if re.search(

        r"\btoday\b",

        question,
    ):

        return (

            today,

            today,

            "Today",
        )


    # =================================================
    # THIS WEEK
    # =================================================

    if "this week" in question:

        start = (

            today -

            timedelta(
                days=
                    today.weekday()
            )
        )


        return (

            start,

            today,

            "This week",
        )


    # =================================================
    # LAST WEEK
    # =================================================

    if "last week" in question:

        current_week_start = (

            today -

            timedelta(
                days=
                    today.weekday()
            )
        )


        end = (

            current_week_start -

            timedelta(
                days=1
            )
        )


        start = (

            end -

            timedelta(
                days=6
            )
        )


        return (

            start,

            end,

            "Last week",
        )


    # =================================================
    # THIS MONTH
    # =================================================

    if "this month" in question:

        return (

            today.replace(
                day=1
            ),

            today,

            "This month",
        )


    # =================================================
    # LAST MONTH
    # =================================================

    if "last month" in question:

        current_month_start = (

            today.replace(
                day=1
            )
        )


        previous_month_end = (

            current_month_start -

            timedelta(
                days=1
            )
        )


        previous_month_start = (

            previous_month_end
            .replace(
                day=1
            )
        )


        return (

            previous_month_start,

            previous_month_end,

            "Last month",
        )


    return None


# =====================================================
# SALES PERIOD SUMMARY
# =====================================================

def sales_period_summary(

    db: Session,

    start_date: date,

    end_date: date,

    label: str,
):

    start_datetime = datetime.combine(

        start_date,

        time.min,
    )


    end_exclusive = datetime.combine(

        end_date +
        timedelta(
            days=1
        ),

        time.min,
    )


    filters = [

        Sale.sale_date >=
        start_datetime,

        Sale.sale_date <
        end_exclusive,
    ]


    orders = (

        db.query(
            Sale
        )

        .filter(
            *filters
        )

        .count()
    )


    revenue = safe_float(

        db.query(

            func.coalesce(

                func.sum(
                    Sale.amount
                ),

                0,
            )
        )

        .filter(
            *filters
        )

        .scalar()
    )


    quantity = safe_int(

        db.query(

            func.coalesce(

                func.sum(
                    Sale.quantity
                ),

                0,
            )
        )

        .filter(
            *filters
        )

        .scalar()
    )


    top_product = (

        db.query(

            Sale.product_name,

            func.sum(
                Sale.amount
            ).label(
                "revenue"
            ),
        )

        .filter(
            *filters
        )

        .group_by(
            Sale.product_name
        )

        .order_by(

            func.sum(
                Sale.amount
            )
            .desc()
        )

        .first()
    )


    if orders == 0:

        return (

            f"{label}: "
            f"no sales records "
            f"were found."
        )


    if (
        start_date ==
        end_date
    ):

        period_text = (

            f"On "
            f"{format_date(start_date)}"
        )

    else:

        period_text = (

            f"From "
            f"{format_date(start_date)} "
            f"to "
            f"{format_date(end_date)}"
        )


    answer = (

        f"{period_text}, "
        f"the business recorded "
        f"{orders} sales/orders "
        f"with revenue of "
        f"{money(revenue)} "
        f"and "
        f"{quantity} units sold."
    )


    if top_product:

        answer += (

            f" The top product by revenue "
            f"in this period was "
            f"{top_product.product_name} "
            f"with "
            f"{money(top_product.revenue)}."
        )


    return answer


# =====================================================
# SPECIFIC PRODUCT ANSWER
# =====================================================

def get_product_answer(
    db: Session,
    question: str,
):

    rows = (

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

            func.count(
                Sale.id
            ).label(
                "orders"
            ),
        )

        .filter(
            Sale.product_name
            .isnot(None)
        )

        .group_by(
            Sale.product_name
        )

        .all()
    )


    for row in rows:

        product_name = (

            row.product_name
            or ""

        ).strip()


        if not product_name:

            continue


        found = re.search(

            rf"\b"
            rf"{re.escape(product_name.lower())}"
            rf"\b",

            question,
        )


        if found:

            return (

                f"{product_name} "
                f"has generated "
                f"{money(row.revenue)} "
                f"from "
                f"{safe_int(row.orders)} "
                f"sales/orders, "
                f"with "
                f"{safe_int(row.quantity)} "
                f"units sold."
            )


    return None


# =====================================================
# SPECIFIC CATEGORY ANSWER
# =====================================================

def get_category_answer(
    db: Session,
    question: str,
):

    rows = (

        db.query(

            Sale.category,

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

            func.count(
                Sale.id
            ).label(
                "orders"
            ),
        )

        .filter(
            Sale.category
            .isnot(None)
        )

        .group_by(
            Sale.category
        )

        .all()
    )


    for row in rows:

        category_name = (

            row.category
            or ""

        ).strip()


        if not category_name:

            continue


        found = re.search(

            rf"\b"
            rf"{re.escape(category_name.lower())}"
            rf"\b",

            question,
        )


        if found:

            return (

                f"The "
                f"{category_name} "
                f"category has generated "
                f"{money(row.revenue)} "
                f"from "
                f"{safe_int(row.orders)} "
                f"sales/orders, "
                f"with "
                f"{safe_int(row.quantity)} "
                f"units sold."
            )


    return None


# =====================================================
# BUSINESS RECOMMENDATION
# =====================================================

def build_recommendation(
    metrics: dict,
):

    recommendations = []


    top_product = metrics.get(
        "top_product"
    )


    top_category = metrics.get(
        "top_category"
    )


    inactive_customers = metrics.get(
        "inactive_customers",
        0,
    )


    if top_product:

        recommendations.append(

            f"Keep sufficient stock of "
            f"{top_product.product_name}, "
            f"your top revenue product."
        )


    if top_category:

        recommendations.append(

            f"Focus marketing on the "
            f"{top_category.category} "
            f"category because it currently "
            f"leads revenue."
        )


    if inactive_customers:

        recommendations.append(

            f"Run a re-engagement campaign "
            f"for "
            f"{inactive_customers} "
            f"inactive customer(s)."
        )


    if not recommendations:

        recommendations.append(

            "Continue adding sales and "
            "customer data so the assistant "
            "can generate stronger insights."
        )


    return (

        "Business recommendation:\n• "

        +

        "\n• ".join(
            recommendations
        )
    )


# =====================================================
# BUSINESS RISK
# =====================================================

def build_risk_answer(
    metrics: dict,
):

    risks = []


    inactive_customers = metrics.get(
        "inactive_customers",
        0,
    )


    total_sales = metrics.get(
        "total_sales",
        0,
    )


    if inactive_customers > 0:

        risks.append(

            f"{inactive_customers} "
            f"customer(s) are inactive."
        )


    if total_sales < 5:

        risks.append(

            "The sales dataset is still "
            "small, so analytics and "
            "forecasts may be less reliable."
        )


    if not risks:

        return (

            "No immediate high-priority "
            "business risk was detected "
            "from the current summary data."
        )


    return (

        "Current business risks:\n• "

        +

        "\n• ".join(
            risks
        )
    )


# =====================================================
# ML FORECAST ANSWER
# =====================================================

def build_forecast_answer(
    db: Session,
    current_user: dict,
):

    forecast_data = sales_forecast(

        db=db,

        current_user=
            current_user,
    )


    summary = forecast_data.get(

        "summary",

        {},
    )


    model_info = forecast_data.get(

        "model_info",

        {},
    )


    forecast_total = summary.get(

        "forecast_7_days",

        0,
    )


    predicted_orders = summary.get(

        "predicted_total_orders",

        0,
    )


    predicted_quantity = summary.get(

        "predicted_total_quantity",

        0,
    )


    method = model_info.get(

        "method",

        "Forecast model",
    )


    quality = model_info.get(

        "model_quality",

        "Not Available",
    )


    confidence = model_info.get(

        "confidence",

        "Not Available",
    )


    trend = model_info.get(

        "trend_direction",

        "Not Available",
    )


    r2_score = model_info.get(
        "revenue_r2_score"
    )


    mae = model_info.get(
        "revenue_mae"
    )


    forecast_start = model_info.get(
        "forecast_start_date"
    )


    forecast_end = model_info.get(
        "forecast_end_date"
    )


    ml_ready = model_info.get(
        "ml_ready",
        False,
    )


    answer = (

        f"The next 7-day forecast is "
        f"{money(forecast_total)} "
        f"in predicted revenue, "
        f"about "
        f"{predicted_orders} "
        f"predicted orders, "
        f"and "
        f"{predicted_quantity} "
        f"predicted units. "

        f"Trend: "
        f"{trend}. "

        f"Method: "
        f"{method}. "

        f"Model quality: "
        f"{quality}. "

        f"Confidence: "
        f"{confidence}."
    )


    if (
        r2_score
        is not None
    ):

        answer += (

            f" R²: "
            f"{safe_float(r2_score):.4f}."
        )


    if (
        mae
        is not None
    ):

        answer += (

            f" MAE: "
            f"{money(mae)}."
        )


    if (
        forecast_start
        and
        forecast_end
    ):

        answer += (

            f" Forecast period: "
            f"{forecast_start} "
            f"to "
            f"{forecast_end}."
        )


    if not ml_ready:

        answer += (

            " The ML model is not fully ready yet, "
            "so the fallback forecasting method "
            "is being used."
        )


    elif (
        str(
            confidence
        ).lower()
        ==
        "low"
    ):

        answer += (

            " The model is working, "
            "but confidence is low, "
            "so use this forecast as "
            "decision support rather "
            "than an exact result."
        )


    return answer


# =====================================================
# GEMINI FALLBACK
# =====================================================

def get_gemini_answer(

    question: str,

    user_details: dict,

    metrics: dict,
):

    api_key = os.getenv(
        "GEMINI_API_KEY",
        "",
    ).strip()


    if (
        not api_key
        or
        genai is None
    ):

        return None


    if metrics.get(
        "top_product"
    ):

        top_product = (

            metrics[
                "top_product"
            ].product_name
        )

    else:

        top_product = "N/A"


    if metrics.get(
        "top_category"
    ):

        top_category = (

            metrics[
                "top_category"
            ].category
        )

    else:

        top_category = "N/A"


    prompt = f"""
You are Enterprise AI Business Copilot.

USER PROFILE
Name: {user_details["full_name"]}
Email: {user_details["email"]}
Role: {user_details["role"]}

CURRENT BUSINESS CONTEXT
Total revenue: {money(metrics["total_revenue"])}
Total sales/orders: {metrics["total_sales"]}
Total quantity sold: {metrics["total_quantity"]}
Total customers: {metrics["total_customers"]}
Active customers: {metrics["active_customers"]}
Inactive customers: {metrics["inactive_customers"]}
Average order value: {money(metrics["average_order"])}
Top product: {top_product}
Top category: {top_category}

IMPORTANT RULES

1. Be friendly and concise.
2. Normally answer in 1 to 4 sentences.
3. You may answer greetings and simple conversation.
4. You may explain basic business and productivity concepts.
5. You may answer simple general questions.
6. If the user writes Tamil or Tanglish, you may reply in simple Tanglish.
7. Never invent business figures.
8. Use only CURRENT BUSINESS CONTEXT for business numbers.
9. If an exact business figure is not available in the context, clearly say so.
10. Do not claim to browse the internet.
11. Stay mainly focused on business assistance.

USER QUESTION

{question}
""".strip()


    try:

        client = genai.Client(
            api_key=api_key
        )


        response = (

            client.models
            .generate_content(

                model=
                    GEMINI_MODEL,

                contents=
                    prompt,
            )
        )


        if response.text:

            answer = (

                response.text
                .strip()
            )


            if answer:

                return answer


    except Exception as error:

        print(

            "Gemini AI fallback error:",

            str(error),
        )


    return None


# =====================================================
# MAIN BUSINESS ANSWER ENGINE
# =====================================================

def build_business_answer(

    question: str,

    db: Session,

    current_user: dict,
):

    q = normalize_text(
        question
    )


    user_details = get_user_details(

        db,

        current_user,
    )


    metrics = get_business_metrics(
        db
    )


    name = user_details[
        "full_name"
    ]


    # =================================================
    # GREETINGS
    # =================================================

    if re.fullmatch(

        r"(hi|hello|hey|hai|hii|"
        r"hello there|hey there)"
        r"[!. ]*",

        q,
    ):

        return (

            f"Hi {name}! 👋 "
            f"Welcome to Enterprise AI "
            f"Business Copilot. "
            f"How can I help with your "
            f"business today?"
        )


    if contains_any(

        q,

        [
            "good morning",
            "good afternoon",
            "good evening",
        ],
    ):

        return (

            f"Hello {name}! 👋 "
            f"I'm ready to help with "
            f"your business data."
        )


    # =================================================
    # USER NAME
    # =================================================

    if contains_any(

        q,

        [
            "what is my name",
            "what's my name",
            "whats my name",
            "tell me my name",
            "who am i",
        ],
    ):

        return (
            f"Your name is {name}."
        )


    # =================================================
    # USER EMAIL
    # =================================================

    if contains_any(

        q,

        [
            "what is my email",
            "what's my email",
            "whats my email",
            "my email",
        ],
    ):

        return (

            f"Your registered email is "
            f"{user_details['email']}."
        )


    # =================================================
    # USER ROLE
    # =================================================

    if contains_any(

        q,

        [
            "what is my role",
            "what's my role",
            "whats my role",
            "my role",
        ],
    ):

        return (

            f"Your current role is "
            f"{user_details['role']}."
        )


    # =================================================
    # WHO ARE YOU
    # =================================================

    if contains_any(

        q,

        [
            "who are you",
            "what are you",
        ],
    ):

        return (

            "I'm Enterprise AI Business Copilot, "
            "your assistant for business analytics, "
            "sales, customers, forecasting, risks "
            "and recommendations."
        )


    # =================================================
    # WHAT CAN YOU DO
    # =================================================

    if contains_any(

        q,

        [
            "what can you do",
            "how can you help",
            "help me",
            "show help",
        ],
    ):

        return (

            "I can answer revenue, sales, "
            "customers, products, categories, "
            "date-wise performance, recent sales, "
            "ML forecasts, risks and recommendations. "
            "I can also handle simple conversation."
        )


    # =================================================
    # HOW ARE YOU
    # =================================================

    if contains_any(

        q,

        [
            "how are you",
            "how r u",
        ],
    ):

        return (

            f"I'm doing well, {name}! "
            f"I'm ready to help with "
            f"your business data."
        )


    # =================================================
    # THANK YOU
    # =================================================

    if contains_any(

        q,

        [
            "thank you",
            "thanks",
            "thank u",
        ],
    ):

        return (

            f"You're welcome, "
            f"{name}! 😊"
        )


    # =================================================
    # BYE
    # =================================================

    if re.fullmatch(

        r"(bye|goodbye|see you|see ya)"
        r"[!. ]*",

        q,
    ):

        return (

            f"Goodbye, "
            f"{name}! 👋 "
            f"Have a productive day."
        )


    # =================================================
    # TODAY DATE
    # =================================================

    if (

        contains_any(

            q,

            [
                "today's date",
                "todays date",
                "date today",
                "what date is today",
            ],
        )

        and

        not has_business_word(
            q
        )
    ):

        return (

            f"Today's date is "
            f"{format_date(date.today())}."
        )


    # =================================================
    # ML FORECAST
    # MUST COME BEFORE GENERIC SALES MATCH
    # =================================================

    if contains_any(

        q,

        [
            "forecast",
            "predict",
            "prediction",
            "next week",
            "next 7 days",
            "future sales",
            "future revenue",
        ],
    ):

        return build_forecast_answer(

            db,

            current_user,
        )


    # =================================================
    # EXACT DATE / DATE RANGE
    # =================================================

    explicit_dates = extract_explicit_dates(
        question
    )


    if (

        explicit_dates

        and

        has_business_word(
            q
        )
    ):

        if len(
            explicit_dates
        ) >= 2:

            start_date = min(

                explicit_dates[0],

                explicit_dates[1],
            )


            end_date = max(

                explicit_dates[0],

                explicit_dates[1],
            )


            return sales_period_summary(

                db,

                start_date,

                end_date,

                "Selected period",
            )


        target_date = (
            explicit_dates[0]
        )


        return sales_period_summary(

            db,

            target_date,

            target_date,

            format_date(
                target_date
            ),
        )


    # =================================================
    # MONTH + YEAR
    # =================================================

    month_period = extract_month_period(
        question
    )


    if (

        month_period

        and

        has_business_word(
            q
        )
    ):

        (
            start_date,
            end_date,
            label,
        ) = month_period


        return sales_period_summary(

            db,

            start_date,

            end_date,

            label,
        )


    # =================================================
    # RELATIVE DATE
    # =================================================

    relative_period = get_relative_period(
        q
    )


    if (

        relative_period

        and

        has_business_word(
            q
        )
    ):

        (
            start_date,
            end_date,
            label,
        ) = relative_period


        return sales_period_summary(

            db,

            start_date,

            end_date,

            label,
        )


    # =================================================
    # RECENT SALES
    # =================================================

    if contains_any(

        q,

        [
            "recent sales",
            "latest sales",
            "last sales",
            "last sale",
            "recent orders",
            "latest orders",
        ],
    ):

        recent_sales = (

            db.query(
                Sale
            )

            .order_by(

                Sale.sale_date
                .desc()
            )

            .limit(
                5
            )

            .all()
        )


        if not recent_sales:

            return (
                "There are no sales records yet."
            )


        lines = [
            "Here are the latest sales:"
        ]


        for sale in recent_sales:

            date_text = (

                sale.sale_date
                .strftime(
                    "%d/%m/%Y"
                )

                if sale.sale_date

                else "N/A"
            )


            lines.append(

                f"• "
                f"{sale.product_name} "
                f"— "
                f"{money(sale.amount)} "
                f"— "
                f"{sale.customer_name or 'Unknown customer'} "
                f"— "
                f"{date_text}"
            )


        return "\n".join(
            lines
        )


    # =================================================
    # HIGHEST SALE
    # =================================================

    if contains_any(

        q,

        [
            "highest sale",
            "largest sale",
            "biggest sale",
        ],
    ):

        highest_sale = (

            db.query(
                Sale
            )

            .order_by(

                Sale.amount
                .desc()
            )

            .first()
        )


        if not highest_sale:

            return (
                "There are no sales records yet."
            )


        return (

            f"The highest single sale is "
            f"{money(highest_sale.amount)} "
            f"for "
            f"{highest_sale.product_name}."
        )


    # =================================================
    # LOWEST SALE
    # =================================================

    if contains_any(

        q,

        [
            "lowest sale",
            "smallest sale",
        ],
    ):

        lowest_sale = (

            db.query(
                Sale
            )

            .order_by(

                Sale.amount
                .asc()
            )

            .first()
        )


        if not lowest_sale:

            return (
                "There are no sales records yet."
            )


        return (

            f"The lowest single sale is "
            f"{money(lowest_sale.amount)} "
            f"for "
            f"{lowest_sale.product_name}."
        )


    # =================================================
    # FOCUS PRODUCT
    # FIXES: "Which product should I focus on?"
    # =================================================

    if contains_any(

        q,

        [
            "which product should i focus on",
            "what product should i focus on",
            "product should i focus on",
            "which product should i promote",
            "which product should i market",
            "product to focus on",
            "focus product",
            "focus on product",
        ],
    ):

        top_product = metrics.get(
            "top_product"
        )


        if not top_product:

            return (

                "There are no sales records yet, "
                "so I cannot recommend a "
                "focus product."
            )


        return (

            f"You should currently focus on "
            f"{top_product.product_name}. "

            f"It is your top product by revenue "
            f"with "
            f"{money(top_product.revenue)} "
            f"in revenue, "
            f"{safe_int(top_product.quantity)} "
            f"units sold, and "
            f"{safe_int(top_product.orders)} "
            f"sales/orders. "

            f"Keep stock available and "
            f"prioritize marketing for "
            f"this product."
        )


    # =================================================
    # TOP PRODUCT
    # =================================================

    if contains_any(

        q,

        [
            "best product",
            "top product",
            "highest product",
            "best selling",
            "best-selling",
            "highest selling product",
        ],
    ):

        top_product = metrics.get(
            "top_product"
        )


        if not top_product:

            return (
                "There are no sales records yet."
            )


        return (

            f"Your top product by revenue is "
            f"{top_product.product_name} "
            f"with "
            f"{money(top_product.revenue)} "
            f"in revenue and "
            f"{safe_int(top_product.quantity)} "
            f"units sold."
        )


    # =================================================
    # FOCUS CATEGORY
    # =================================================

    if contains_any(

        q,

        [
            "which category should i focus on",
            "what category should i focus on",
            "category should i focus on",
            "category to focus on",
            "focus category",
        ],
    ):

        top_category = metrics.get(
            "top_category"
        )


        if not top_category:

            return (

                "There are no categorized "
                "sales records yet."
            )


        return (

            f"You should currently focus on "
            f"the "
            f"{top_category.category} "
            f"category. "

            f"It leads revenue with "
            f"{money(top_category.revenue)}, "
            f"{safe_int(top_category.quantity)} "
            f"units sold, and "
            f"{safe_int(top_category.orders)} "
            f"sales/orders."
        )


    # =================================================
    # TOP CATEGORY
    # =================================================

    if contains_any(

        q,

        [
            "best category",
            "top category",
            "highest category",
            "strongest category",
        ],
    ):

        top_category = metrics.get(
            "top_category"
        )


        if not top_category:

            return (

                "There are no categorized "
                "sales records yet."
            )


        return (

            f"Your top category by revenue is "
            f"{top_category.category} "
            f"with "
            f"{money(top_category.revenue)}."
        )


    # =================================================
    # SPECIFIC PRODUCT
    # =================================================

    product_answer = get_product_answer(

        db,

        q,
    )


    if product_answer:

        return product_answer


    # =================================================
    # SPECIFIC CATEGORY
    # =================================================

    category_answer = get_category_answer(

        db,

        q,
    )


    if category_answer:

        return category_answer


    # =================================================
    # BUSINESS RECOMMENDATION
    # =================================================

    if contains_any(

        q,

        [
            "recommend",
            "recommendation",
            "suggestion",
            "what should i do",
            "improve business",
            "increase business",
            "grow business",
            "increase revenue",
            "boost revenue",
        ],
    ):

        return build_recommendation(
            metrics
        )


    # =================================================
    # BUSINESS RISK
    # =================================================

    if contains_any(

        q,

        [
            "risk",
            "risks",
            "business risk",
            "problem",
            "warning",
        ],
    ):

        return build_risk_answer(
            metrics
        )


    # =================================================
    # PROFIT
    # =================================================

    if contains_any(

        q,

        [
            "profit",
            "margin",
            "gross profit",
            "net profit",
        ],
    ):

        return (

            "I can calculate revenue from "
            "the current sales data, but "
            "exact profit cannot be calculated "
            "because product cost/expense data "
            "is not available."
        )


    # =================================================
    # INACTIVE CUSTOMERS
    # =================================================

    if contains_any(

        q,

        [
            "inactive customer",
            "inactive customers",
        ],
    ):

        return (

            f"You currently have "
            f"{metrics['inactive_customers']} "
            f"inactive customer(s)."
        )


    # =================================================
    # ACTIVE CUSTOMERS
    # =================================================

    if contains_any(

        q,

        [
            "active customer",
            "active customers",
        ],
    ):

        return (

            f"You currently have "
            f"{metrics['active_customers']} "
            f"active customer(s)."
        )


    # =================================================
    # TOTAL CUSTOMERS
    # =================================================

    if contains_any(

        q,

        [
            "customer",
            "customers",
            "client",
            "clients",
        ],
    ):

        return (

            f"You have "
            f"{metrics['total_customers']} "
            f"customers: "
            f"{metrics['active_customers']} "
            f"active and "
            f"{metrics['inactive_customers']} "
            f"inactive."
        )


    # =================================================
    # AVERAGE ORDER VALUE
    # =================================================

    if contains_any(

        q,

        [
            "average order value",
            "aov",
            "average sale",
            "average order",
        ],
    ):

        return (

            f"Your average order value is "
            f"{money(metrics['average_order'])}. "
            f"This is based on "
            f"{metrics['total_sales']} "
            f"sales/orders."
        )


    # =================================================
    # TOTAL QUANTITY
    # =================================================

    if contains_any(

        q,

        [
            "quantity",
            "units sold",
            "how many units",
        ],
    ):

        return (

            f"The total quantity sold is "
            f"{metrics['total_quantity']} "
            f"units across "
            f"{metrics['total_sales']} "
            f"sales/orders."
        )


    # =================================================
    # TOTAL SALES
    # =================================================

    if contains_any(

        q,

        [
            "how many sales",
            "order count",
            "total sales",
            "total orders",
            "sales count",
            "orders count",
        ],
    ):

        return (

            f"You currently have "
            f"{metrics['total_sales']} "
            f"sales/orders. "

            f"Total quantity sold is "
            f"{metrics['total_quantity']} "
            f"units and total revenue is "
            f"{money(metrics['total_revenue'])}."
        )


    # =================================================
    # TOTAL REVENUE
    # =================================================

    if contains_any(

        q,

        [
            "revenue",
            "income",
            "turnover",
        ],
    ):

        return (

            f"Your total business revenue is "
            f"{money(metrics['total_revenue'])}. "

            f"You have "
            f"{metrics['total_sales']} "
            f"sales/orders with an average "
            f"order value of "
            f"{money(metrics['average_order'])}."
        )


    # =================================================
    # GENERIC SALES / ORDERS
    # =================================================

    if contains_any(

        q,

        [
            "sales",
            "orders",
        ],
    ):

        return (

            f"You currently have "
            f"{metrics['total_sales']} "
            f"sales/orders. "

            f"Total quantity sold is "
            f"{metrics['total_quantity']} "
            f"units and total revenue is "
            f"{money(metrics['total_revenue'])}."
        )


    # =================================================
    # BUSINESS SUMMARY
    # =================================================

    if contains_any(

        q,

        [
            "business summary",
            "summary",
            "overview",
            "business status",
        ],
    ):

        return (

            "Current business summary:\n"

            f"• Revenue: "
            f"{money(metrics['total_revenue'])}\n"

            f"• Sales/Orders: "
            f"{metrics['total_sales']}\n"

            f"• Quantity sold: "
            f"{metrics['total_quantity']}\n"

            f"• Customers: "
            f"{metrics['total_customers']}\n"

            f"• Active customers: "
            f"{metrics['active_customers']}\n"

            f"• Inactive customers: "
            f"{metrics['inactive_customers']}\n"

            f"• Average order value: "
            f"{money(metrics['average_order'])}"
        )


    # =================================================
    # GEMINI FALLBACK
    # =================================================

    gemini_answer = get_gemini_answer(

        question,

        user_details,

        metrics,
    )


    if gemini_answer:

        return gemini_answer


    # =================================================
    # SAFE LOCAL FALLBACK
    # =================================================

    return (

        f"I'm your Enterprise AI Business "
        f"Copilot, {name}. "

        f"I can help with sales, revenue, "
        f"customers, products, categories, "
        f"date-wise performance, ML forecasts, "
        f"risks and recommendations. "

        f"Try asking "
        f"'Which product should I focus on?', "
        f"'What is my next 7 days sales forecast?', "
        f"or "
        f"'Give me a business recommendation.'"
    )


# =====================================================
# CHAT API
# =====================================================

@router.post(
    "/chat"
)
def ai_chat(

    request: ChatRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: dict = Depends(
        get_current_user
    ),
):

    message = (

        request.message
        .strip()
    )


    if not message:

        raise HTTPException(

            status_code=400,

            detail=
                "Message cannot be empty",
        )


    answer = build_business_answer(

        message,

        db,

        current_user,
    )


    return {

        "message":
            message,

        "answer":
            answer,

        "user_id":
            current_user.get(
                "sub"
            ),

        "email":
            current_user.get(
                "email"
            ),
    }