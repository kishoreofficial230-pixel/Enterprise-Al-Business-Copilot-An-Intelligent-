from collections import defaultdict
from datetime import date, datetime, timedelta
import calendar
import os
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from dotenv import load_dotenv

    load_dotenv()

except ImportError:
    pass


try:
    from google import genai

except ImportError:
    genai = None


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
# REQUEST
# =====================================================

class ChatRequest(BaseModel):

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )


# =====================================================
# SETTINGS
# =====================================================

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash",
)


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
    "categories",

    "customer",
    "customers",

    "client",
    "clients",

    "invoice",
    "invoices",

    "gst",
    "cgst",
    "sgst",
    "igst",

    "tax",
    "taxable",

    "forecast",
    "predict",
    "prediction",

    "growth",
    "decline",
    "performance",

    "profit",
    "margin",

    "hsn",

    "stock",

    "recommend",

    "risk",

    "health",
}


# =====================================================
# BASIC HELPERS
# =====================================================

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


def money(
    value,
):

    return (
        f"₹{safe_float(value):,.2f}"
    )


def format_date(
    value,
):

    if value is None:

        return "N/A"


    if isinstance(
        value,
        datetime,
    ):

        value = value.date()


    return value.strftime(
        "%d %B %Y"
    )


def sale_date_value(
    sale,
):

    value = getattr(
        sale,
        "sale_date",
        None,
    )


    if isinstance(
        value,
        datetime,
    ):

        return value


    return None


def sale_amount(
    sale,
):

    return safe_float(
        getattr(
            sale,
            "amount",
            0,
        )
    )


def sale_quantity(
    sale,
):

    return safe_int(
        getattr(
            sale,
            "quantity",
            0,
        )
    )


def clean_name(
    value,
    fallback="Unknown",
):

    text = str(
        value or ""
    ).strip()


    return (
        text
        or fallback
    )


def percent_change(
    current,
    previous,
):

    current = safe_float(
        current
    )

    previous = safe_float(
        previous
    )


    if previous == 0:

        if current == 0:

            return 0.0


        return None


    return (
        (
            current -
            previous
        )
        /
        previous
    ) * 100


# =====================================================
# USER DETAILS
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
# DATE PARSING
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


    for format_string in formats:

        try:

            return datetime.strptime(

                cleaned,

                format_string,

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


    result = []


    for _, parsed in found:

        if parsed not in result:

            result.append(
                parsed
            )


    return result


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


    month_text = match.group(
        1
    )


    year = int(
        match.group(
            2
        )
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


def extract_year_period(
    text: str,
):

    matches = re.findall(

        r"\b(20\d{2})\b",

        text,
    )


    if not matches:

        return None


    year = int(
        matches[0]
    )


    return (

        date(
            year,
            1,
            1,
        ),

        date(
            year,
            12,
            31,
        ),

        str(
            year
        ),
    )


def get_relative_period(
    question: str,
):

    q = normalize_text(
        question
    )


    today = date.today()


    last_days_match = re.search(

        r"\b(?:last|past)"
        r"\s+"
        r"(\d{1,3})"
        r"\s+days?\b",

        q,
    )


    if last_days_match:

        days = max(

            1,

            int(
                last_days_match
                .group(
                    1
                )
            ),
        )


        return (

            today -
            timedelta(
                days=
                    days -
                    1
            ),

            today,

            f"Last {days} days",
        )


    if "yesterday" in q:

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


    if re.search(
        r"\btoday\b",
        q,
    ):

        return (

            today,

            today,

            "Today",
        )


    if "this week" in q:

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


    if "last week" in q:

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


    if "this month" in q:

        return (

            today.replace(
                day=1
            ),

            today,

            "This month",
        )


    if "last month" in q:

        current_month_start = (

            today.replace(
                day=1
            )
        )


        end = (

            current_month_start -

            timedelta(
                days=1
            )
        )


        start = (

            end.replace(
                day=1
            )
        )


        return (

            start,

            end,

            "Last month",
        )


    if "this year" in q:

        return (

            date(
                today.year,
                1,
                1,
            ),

            today,

            "This year",
        )


    if "last year" in q:

        year = (
            today.year -
            1
        )


        return (

            date(
                year,
                1,
                1,
            ),

            date(
                year,
                12,
                31,
            ),

            "Last year",
        )


    return None


def resolve_period(
    question: str,
):

    explicit_dates = extract_explicit_dates(
        question
    )


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


        return (

            start_date,

            end_date,

            "Selected period",
        )


    if len(
        explicit_dates
    ) == 1:

        target_date = (
            explicit_dates[0]
        )


        return (

            target_date,

            target_date,

            format_date(
                target_date
            ),
        )


    month_period = extract_month_period(
        question
    )


    if month_period:

        return month_period


    relative_period = get_relative_period(
        question
    )


    if relative_period:

        return relative_period


    if has_business_word(
        normalize_text(
            question
        )
    ):

        year_period = extract_year_period(
            question
        )


        if year_period:

            return year_period


    return None


def rows_in_period(
    rows,
    start_date,
    end_date,
):

    result = []


    for sale in rows:

        sale_datetime = sale_date_value(
            sale
        )


        if (

            sale_datetime

            and

            start_date
            <=
            sale_datetime.date()
            <=
            end_date

        ):

            result.append(
                sale
            )


    return result


# =====================================================
# AGGREGATION
# =====================================================

def aggregate_rows(
    rows,
    key_function,
):

    grouped = defaultdict(
        lambda: {

            "revenue":
                0.0,

            "quantity":
                0,

            "orders":
                0,

            "taxable":
                0.0,

            "cgst":
                0.0,

            "sgst":
                0.0,

            "igst":
                0.0,
        }
    )


    for sale in rows:

        key = key_function(
            sale
        )


        if key in (
            None,
            "",
        ):

            continue


        data = grouped[
            key
        ]


        data[
            "revenue"
        ] += sale_amount(
            sale
        )


        data[
            "quantity"
        ] += sale_quantity(
            sale
        )


        data[
            "orders"
        ] += 1


        data[
            "taxable"
        ] += safe_float(

            getattr(
                sale,
                "taxable_amount",
                0,
            )
        )


        data[
            "cgst"
        ] += safe_float(

            getattr(
                sale,
                "cgst",
                0,
            )
        )


        data[
            "sgst"
        ] += safe_float(

            getattr(
                sale,
                "sgst",
                0,
            )
        )


        data[
            "igst"
        ] += safe_float(

            getattr(
                sale,
                "igst",
                0,
            )
        )


    return dict(
        grouped
    )


def ranked(
    grouped,
    metric="revenue",
    reverse=True,
):

    return sorted(

        [
            (
                key,
                data,
            )

            for key, data
            in grouped.items()
        ],

        key=lambda item: (

            safe_float(
                item[1].get(
                    metric
                )
            ),

            str(
                item[0]
            ).lower(),
        ),

        reverse=
            reverse,
    )


def matched_entities(
    question,
    names,
):

    q = normalize_text(
        question
    )


    result = []


    sorted_names = sorted(

        [
            str(
                name
            )

            for name
            in names
        ],

        key=len,

        reverse=True,
    )


    for name in sorted_names:

        normalized_name = normalize_text(
            name
        )


        if (

            normalized_name

            and

            re.search(

                rf"(?<!\w)"
                rf"{re.escape(normalized_name)}"
                rf"(?!\w)",

                q,
            )

        ):

            result.append(
                name
            )


    return list(
        dict.fromkeys(
            result
        )
    )


def sale_period_summary(
    rows,
    label,
):

    if not rows:

        return (

            f"{label}: "
            f"no sales records "
            f"were found."
        )


    revenue = sum(

        sale_amount(
            sale
        )

        for sale
        in rows
    )


    quantity = sum(

        sale_quantity(
            sale
        )

        for sale
        in rows
    )


    product_groups = aggregate_rows(

        rows,

        lambda sale:
            clean_name(

                getattr(
                    sale,
                    "product_name",
                    None,
                )
            ),
    )


    top_product = ranked(

        product_groups,

        "revenue",

    )[:1]


    answer = (

        f"{label}: "
        f"{len(rows)} "
        f"sales/orders, "
        f"{quantity} "
        f"units sold, "
        f"and recorded revenue of "
        f"{money(revenue)}."
    )


    if top_product:

        product_name, data = (
            top_product[0]
        )


        answer += (

            f" Top product by revenue: "
            f"{product_name} "
            f"({money(data['revenue'])})."
        )


    return answer


def build_snapshot(
    db: Session,
):

    sales = (

        db.query(
            Sale
        )

        .order_by(

            Sale.sale_date
            .asc(),

            Sale.id
            .asc(),
        )

        .all()
    )


    customers = (

        db.query(
            Customer
        )

        .all()
    )


    product_groups = aggregate_rows(

        sales,

        lambda sale:
            clean_name(

                getattr(
                    sale,
                    "product_name",
                    None,
                )
            ),
    )


    category_groups = aggregate_rows(

        sales,

        lambda sale:
            clean_name(

                getattr(
                    sale,
                    "category",
                    None,
                ),

                "Uncategorized",
            ),
    )


    customer_groups = aggregate_rows(

        sales,

        lambda sale:
            (
                str(

                    getattr(
                        sale,
                        "customer_name",
                        "",
                    )

                    or ""

                ).strip()

                or None
            ),
    )


    date_groups = aggregate_rows(

        sales,

        lambda sale:
            (
                sale_date_value(
                    sale
                ).date()

                if sale_date_value(
                    sale
                )

                else None
            ),
    )


    month_groups = aggregate_rows(

        sales,

        lambda sale:
            (
                sale_date_value(
                    sale
                ).strftime(
                    "%Y-%m"
                )

                if sale_date_value(
                    sale
                )

                else None
            ),
    )


    hsn_groups = aggregate_rows(

        sales,

        lambda sale:
            (
                str(

                    getattr(
                        sale,
                        "hsn_code",
                        "",
                    )

                    or ""

                ).strip()

                or None
            ),
    )


    total_revenue = sum(

        sale_amount(
            sale
        )

        for sale
        in sales
    )


    total_quantity = sum(

        sale_quantity(
            sale
        )

        for sale
        in sales
    )


    total_sales = len(
        sales
    )


    total_customers = len(
        customers
    )


    active_customers = sum(

        1

        for customer
        in customers

        if normalize_text(

            getattr(
                customer,
                "status",
                "",
            )
        )
        ==
        "active"
    )


    inactive_customers = sum(

        1

        for customer
        in customers

        if normalize_text(

            getattr(
                customer,
                "status",
                "",
            )
        )
        ==
        "inactive"
    )


    total_cgst = sum(

        safe_float(

            getattr(
                sale,
                "cgst",
                0,
            )
        )

        for sale
        in sales
    )


    total_sgst = sum(

        safe_float(

            getattr(
                sale,
                "sgst",
                0,
            )
        )

        for sale
        in sales
    )


    total_igst = sum(

        safe_float(

            getattr(
                sale,
                "igst",
                0,
            )
        )

        for sale
        in sales
    )


    total_gst = (

        total_cgst
        +
        total_sgst
        +
        total_igst
    )


    invoice_rows = [

        sale

        for sale
        in sales

        if getattr(
            sale,
            "invoice_number",
            None,
        )
    ]


    legacy_rows = [

        sale

        for sale
        in sales

        if not getattr(
            sale,
            "invoice_number",
            None,
        )
    ]


    return {

        "sales":
            sales,

        "customers":
            customers,

        "product_groups":
            product_groups,

        "category_groups":
            category_groups,

        "customer_groups":
            customer_groups,

        "date_groups":
            date_groups,

        "month_groups":
            month_groups,

        "hsn_groups":
            hsn_groups,

        "total_revenue":
            total_revenue,

        "total_quantity":
            total_quantity,

        "total_sales":
            total_sales,

        "total_customers":
            total_customers,

        "active_customers":
            active_customers,

        "inactive_customers":
            inactive_customers,

        "average_order":
            (
                total_revenue /
                total_sales

                if total_sales

                else 0
            ),

        "total_cgst":
            total_cgst,

        "total_sgst":
            total_sgst,

        "total_igst":
            total_igst,

        "total_gst":
            total_gst,

        "invoice_rows":
            invoice_rows,

        "legacy_rows":
            legacy_rows,
    }


# =====================================================
# RANKING HELPERS
# =====================================================

def rank_answer(
    grouped,
    entity_label,
    metric,
    highest=True,
):

    rows = ranked(

        grouped,

        metric,

        reverse=
            highest,
    )


    if not rows:

        return (

            f"There are no "
            f"{entity_label.lower()} "
            f"records to analyze yet."
        )


    name, data = (
        rows[0]
    )


    direction = (

        "highest"

        if highest

        else "lowest"
    )


    metric_label = {

        "revenue":
            "revenue",

        "quantity":
            "quantity sold",

        "orders":
            "order count",

    }[
        metric
    ]


    return (

        f"The "
        f"{entity_label.lower()} "
        f"with the "
        f"{direction} "
        f"{metric_label} "
        f"is "
        f"{name}: "
        f"{money(data['revenue'])} "
        f"revenue, "
        f"{safe_int(data['quantity'])} "
        f"units, and "
        f"{safe_int(data['orders'])} "
        f"orders."
    )


def top_n_answer(
    grouped,
    entity_label,
    metric,
    n=5,
    highest=True,
):

    rows = ranked(

        grouped,

        metric,

        reverse=
            highest,

    )[:n]


    if not rows:

        return (

            f"There are no "
            f"{entity_label.lower()} "
            f"records to rank yet."
        )


    metric_label = {

        "revenue":
            "revenue",

        "quantity":
            "units",

        "orders":
            "orders",

    }[
        metric
    ]


    heading = (

        "Top"

        if highest

        else "Bottom"
    )


    lines = [

        f"{heading} "
        f"{len(rows)} "
        f"{entity_label.lower()} "
        f"by "
        f"{metric_label}:"
    ]


    for index, (
        name,
        data,
    ) in enumerate(
        rows,
        start=1,
    ):

        lines.append(

            f"{index}. "
            f"{name} "
            f"— "
            f"{money(data['revenue'])}, "
            f"{safe_int(data['quantity'])} "
            f"units, "
            f"{safe_int(data['orders'])} "
            f"orders"
        )


    return "\n".join(
        lines
    )


def specific_group_answer(
    name,
    data,
    entity_label,
):

    return (

        f"{entity_label} "
        f"{name}: "
        f"{money(data['revenue'])} "
        f"revenue from "
        f"{safe_int(data['orders'])} "
        f"orders, with "
        f"{safe_int(data['quantity'])} "
        f"units sold."
    )


def compare_entities(
    grouped,
    names,
    entity_label,
):

    if len(
        names
    ) < 2:

        return None


    first = names[0]

    second = names[1]


    first_data = grouped.get(
        first
    )


    second_data = grouped.get(
        second
    )


    if (
        not first_data
        or
        not second_data
    ):

        return None


    if (
        first_data[
            "revenue"
        ]
        >
        second_data[
            "revenue"
        ]
    ):

        revenue_winner = first

    elif (
        second_data[
            "revenue"
        ]
        >
        first_data[
            "revenue"
        ]
    ):

        revenue_winner = second

    else:

        revenue_winner = "Tie"


    if (
        first_data[
            "quantity"
        ]
        >
        second_data[
            "quantity"
        ]
    ):

        quantity_winner = first

    elif (
        second_data[
            "quantity"
        ]
        >
        first_data[
            "quantity"
        ]
    ):

        quantity_winner = second

    else:

        quantity_winner = "Tie"


    return (

        f"{entity_label} comparison:\n"

        f"• {first}: "
        f"{money(first_data['revenue'])}, "
        f"{safe_int(first_data['quantity'])} units, "
        f"{safe_int(first_data['orders'])} orders\n"

        f"• {second}: "
        f"{money(second_data['revenue'])}, "
        f"{safe_int(second_data['quantity'])} units, "
        f"{safe_int(second_data['orders'])} orders\n"

        f"Revenue leader: "
        f"{revenue_winner}. "

        f"Quantity leader: "
        f"{quantity_winner}."
    )


# =====================================================
# DATE / MONTH ANALYSIS
# =====================================================

def best_date_answer(
    snapshot,
    highest=True,
    metric="revenue",
):

    rows = ranked(

        snapshot[
            "date_groups"
        ],

        metric,

        reverse=
            highest,
    )


    if not rows:

        return (

            "There are no dated "
            "sales records to "
            "analyze yet."
        )


    sale_day, data = (
        rows[0]
    )


    direction = (

        "highest"

        if highest

        else "lowest"
    )


    metric_text = {

        "revenue":
            "revenue",

        "quantity":
            "quantity sold",

        "orders":
            "order count",

    }[
        metric
    ]


    return (

        f"The date with the "
        f"{direction} "
        f"{metric_text} "
        f"was "
        f"{format_date(sale_day)}: "
        f"{money(data['revenue'])} "
        f"revenue, "
        f"{safe_int(data['orders'])} "
        f"orders, and "
        f"{safe_int(data['quantity'])} "
        f"units."
    )


def best_month_answer(
    snapshot,
    highest=True,
    metric="revenue",
):

    rows = ranked(

        snapshot[
            "month_groups"
        ],

        metric,

        reverse=
            highest,
    )


    if not rows:

        return (

            "There are no dated "
            "sales records to "
            "analyze by month yet."
        )


    month_key, data = (
        rows[0]
    )


    month_label = (

        datetime.strptime(

            month_key,

            "%Y-%m",

        ).strftime(
            "%B %Y"
        )
    )


    direction = (

        "highest"

        if highest

        else "lowest"
    )


    metric_text = {

        "revenue":
            "revenue",

        "quantity":
            "quantity sold",

        "orders":
            "order count",

    }[
        metric
    ]


    return (

        f"The month with the "
        f"{direction} "
        f"{metric_text} "
        f"was "
        f"{month_label}: "
        f"{money(data['revenue'])} "
        f"revenue, "
        f"{safe_int(data['orders'])} "
        f"orders, and "
        f"{safe_int(data['quantity'])} "
        f"units."
    )


def compare_periods(
    snapshot,
    first,
    second,
):

    (
        first_start,
        first_end,
        first_label,
    ) = first


    (
        second_start,
        second_end,
        second_label,
    ) = second


    first_rows = rows_in_period(

        snapshot[
            "sales"
        ],

        first_start,

        first_end,
    )


    second_rows = rows_in_period(

        snapshot[
            "sales"
        ],

        second_start,

        second_end,
    )


    first_revenue = sum(

        sale_amount(
            sale
        )

        for sale
        in first_rows
    )


    second_revenue = sum(

        sale_amount(
            sale
        )

        for sale
        in second_rows
    )


    first_quantity = sum(

        sale_quantity(
            sale
        )

        for sale
        in first_rows
    )


    second_quantity = sum(

        sale_quantity(
            sale
        )

        for sale
        in second_rows
    )


    if (
        first_revenue
        >
        second_revenue
    ):

        leader = first_label


    elif (
        second_revenue
        >
        first_revenue
    ):

        leader = second_label


    else:

        leader = "Tie"


    change = percent_change(

        first_revenue,

        second_revenue,
    )


    if change is None:

        change_line = (

            "Percentage change cannot "
            "be calculated because the "
            "comparison-period revenue "
            "is zero."
        )

    else:

        change_line = (

            f"Relative change "
            f"({first_label} vs "
            f"{second_label}): "
            f"{change:+.2f}%."
        )


    return (

        f"Period comparison:\n"

        f"• {first_label}: "
        f"{money(first_revenue)}, "
        f"{len(first_rows)} orders, "
        f"{first_quantity} units\n"

        f"• {second_label}: "
        f"{money(second_revenue)}, "
        f"{len(second_rows)} orders, "
        f"{second_quantity} units\n"

        f"Revenue leader: "
        f"{leader}. "

        f"{change_line}"
    )


def common_period_comparison(
    question,
):

    q = normalize_text(
        question
    )


    today = date.today()


    if (
        "this month" in q
        and
        "last month" in q
    ):

        this_month = (

            today.replace(
                day=1
            ),

            today,

            "This month",
        )


        previous_end = (

            today.replace(
                day=1
            )

            -

            timedelta(
                days=1
            )
        )


        last_month = (

            previous_end.replace(
                day=1
            ),

            previous_end,

            "Last month",
        )


        return (

            this_month,

            last_month,
        )


    if (
        "this week" in q
        and
        "last week" in q
    ):

        this_start = (

            today -

            timedelta(
                days=
                    today.weekday()
            )
        )


        this_week = (

            this_start,

            today,

            "This week",
        )


        last_end = (

            this_start -

            timedelta(
                days=1
            )
        )


        last_week = (

            last_end -

            timedelta(
                days=6
            ),

            last_end,

            "Last week",
        )


        return (

            this_week,

            last_week,
        )


    if (
        "this year" in q
        and
        "last year" in q
    ):

        this_year = (

            date(
                today.year,
                1,
                1,
            ),

            today,

            "This year",
        )


        previous_year = (
            today.year -
            1
        )


        last_year = (

            date(
                previous_year,
                1,
                1,
            ),

            date(
                previous_year,
                12,
                31,
            ),

            "Last year",
        )


        return (

            this_year,

            last_year,
        )


    return None


def growth_snapshot(
    snapshot,
):

    today = date.today()


    current_start = (

        today -

        timedelta(
            days=29
        )
    )


    previous_end = (

        current_start -

        timedelta(
            days=1
        )
    )


    previous_start = (

        previous_end -

        timedelta(
            days=29
        )
    )


    current_rows = rows_in_period(

        snapshot[
            "sales"
        ],

        current_start,

        today,
    )


    previous_rows = rows_in_period(

        snapshot[
            "sales"
        ],

        previous_start,

        previous_end,
    )


    current_revenue = sum(

        sale_amount(
            sale
        )

        for sale
        in current_rows
    )


    previous_revenue = sum(

        sale_amount(
            sale
        )

        for sale
        in previous_rows
    )


    change = percent_change(

        current_revenue,

        previous_revenue,
    )


    if change is None:

        change_value = (

            "N/A because the "
            "previous 30-day "
            "revenue was zero"
        )

    else:

        change_value = (
            f"{change:+.2f}%"
        )


    return (

        f"Last 30 days revenue: "
        f"{money(current_revenue)}. "

        f"Previous 30 days: "
        f"{money(previous_revenue)}. "

        f"Revenue change: "
        f"{change_value}."
    )


# =====================================================
# INVOICE / GST
# =====================================================

def invoice_answer(
    snapshot,
    question,
):

    match = re.search(

        r"\bINV-\d+\b",

        question,

        flags=re.IGNORECASE,
    )


    if not match:

        return None


    invoice_number = (

        match.group(0)
        .upper()
    )


    sale = next(

        (

            row

            for row
            in snapshot[
                "sales"
            ]

            if str(

                getattr(
                    row,
                    "invoice_number",
                    "",
                )

                or ""

            ).upper()
            ==
            invoice_number
        ),

        None,
    )


    if not sale:

        return (

            f"Invoice "
            f"{invoice_number} "
            f"was not found."
        )


    return (

        f"Invoice "
        f"{invoice_number}: "

        f"{clean_name(getattr(sale, 'product_name', None))}, "

        f"quantity "
        f"{sale_quantity(sale)}, "

        f"unit price "
        f"{money(getattr(sale, 'unit_price', 0))}, "

        f"taxable amount "
        f"{money(getattr(sale, 'taxable_amount', 0))}, "

        f"GST "
        f"{safe_float(getattr(sale, 'gst_percent', 0)):.2f}%, "

        f"CGST "
        f"{money(getattr(sale, 'cgst', 0))}, "

        f"SGST "
        f"{money(getattr(sale, 'sgst', 0))}, "

        f"IGST "
        f"{money(getattr(sale, 'igst', 0))}, "

        f"final amount "
        f"{money(getattr(sale, 'final_amount', None) or sale_amount(sale))}. "

        f"Customer: "
        f"{clean_name(getattr(sale, 'customer_name', None), 'N/A')}. "

        f"Date: "
        f"{format_date(sale_date_value(sale))}."
    )


def gst_answer(
    snapshot,
    question,
):

    q = normalize_text(
        question
    )


    if contains_any(

        q,

        [
            "total cgst",
            "cgst collected",
            "cgst total",
        ],
    ):

        return (

            f"Total recorded CGST is "
            f"{money(snapshot['total_cgst'])}."
        )


    if contains_any(

        q,

        [
            "total sgst",
            "sgst collected",
            "sgst total",
        ],
    ):

        return (

            f"Total recorded SGST is "
            f"{money(snapshot['total_sgst'])}."
        )


    if contains_any(

        q,

        [
            "total igst",
            "igst collected",
            "igst total",
        ],
    ):

        return (

            f"Total recorded IGST is "
            f"{money(snapshot['total_igst'])}."
        )


    if contains_any(

        q,

        [
            "gst",
            "tax",
        ],
    ):

        return (

            f"Recorded GST total is "
            f"{money(snapshot['total_gst'])}: "

            f"CGST "
            f"{money(snapshot['total_cgst'])}, "

            f"SGST "
            f"{money(snapshot['total_sgst'])}, "

            f"and IGST "
            f"{money(snapshot['total_igst'])}. "

            f"This is based on "
            f"{len(snapshot['invoice_rows'])} "
            f"GST/invoice sale(s). "

            f"{len(snapshot['legacy_rows'])} "
            f"legacy sale(s) do not contain "
            f"the new GST fields."
        )


    return None


# =====================================================
# CUSTOMER HELPERS
# =====================================================

def customer_status_answer(
    snapshot,
    status,
    list_names=False,
):

    customers = [

        customer

        for customer
        in snapshot[
            "customers"
        ]

        if normalize_text(

            getattr(
                customer,
                "status",
                "",
            )
        )
        ==
        status
    ]


    if not list_names:

        return (

            f"You currently have "
            f"{len(customers)} "
            f"{status} "
            f"customer(s)."
        )


    if not customers:

        return (

            f"There are no "
            f"{status} customers."
        )


    names = [

        clean_name(

            getattr(
                customer,
                "full_name",
                None,
            )
        )

        for customer
        in customers[:20]
    ]


    extra = (

        len(customers) -
        len(names)
    )


    answer = (

        f"{status.title()} customers: "
        +
        ", ".join(
            names
        )
    )


    if extra > 0:

        answer += (

            f" and "
            f"{extra} more"
        )


    return (
        answer +
        "."
    )


def new_customer_period_answer(
    snapshot,
    period,
):

    (
        start_date,
        end_date,
        label,
    ) = period


    matched = []


    for customer in snapshot[
        "customers"
    ]:

        created_at = getattr(

            customer,

            "created_at",

            None,
        )


        if (

            isinstance(
                created_at,
                datetime,
            )

            and

            start_date
            <=
            created_at.date()
            <=
            end_date

        ):

            matched.append(
                customer
            )


    return (

        f"{label}: "
        f"{len(matched)} "
        f"new customer(s) "
        f"were registered."
    )


# =====================================================
# RECOMMENDATION / RISK
# =====================================================

def build_recommendation(
    snapshot,
):

    recommendations = []


    top_products = ranked(

        snapshot[
            "product_groups"
        ],

        "revenue",
    )


    bottom_products = ranked(

        snapshot[
            "product_groups"
        ],

        "revenue",

        reverse=False,
    )


    top_categories = ranked(

        snapshot[
            "category_groups"
        ],

        "revenue",
    )


    if top_products:

        name, data = (
            top_products[0]
        )


        recommendations.append(

            f"Protect stock availability "
            f"for {name}, your top "
            f"revenue product at "
            f"{money(data['revenue'])}."
        )


    if top_categories:

        name, data = (
            top_categories[0]
        )


        recommendations.append(

            f"Prioritize campaigns in "
            f"{name}, your leading "
            f"category at "
            f"{money(data['revenue'])}."
        )


    if len(
        bottom_products
    ) > 1:

        name, data = (
            bottom_products[0]
        )


        recommendations.append(

            f"Review {name}; "
            f"it is currently one "
            f"of the weakest products "
            f"at "
            f"{money(data['revenue'])} "
            f"revenue."
        )


    if snapshot[
        "inactive_customers"
    ] > 0:

        recommendations.append(

            f"Run a re-engagement "
            f"campaign for "
            f"{snapshot['inactive_customers']} "
            f"inactive customer(s)."
        )


    if not recommendations:

        recommendations.append(

            "Add more sales and "
            "customer data to "
            "generate stronger "
            "recommendations."
        )


    return (

        "Business recommendations:\n• "

        +

        "\n• ".join(
            recommendations
        )
    )


def build_risk_answer(
    snapshot,
):

    risks = []


    if snapshot[
        "inactive_customers"
    ] > 0:

        risks.append(

            f"{snapshot['inactive_customers']} "
            f"customer(s) are inactive."
        )


    if snapshot[
        "total_sales"
    ] < 5:

        risks.append(

            "The sales dataset is still "
            "small, so analytics and "
            "forecasts may be unstable."
        )


    top_products = ranked(

        snapshot[
            "product_groups"
        ],

        "revenue",
    )


    if (

        top_products

        and

        snapshot[
            "total_revenue"
        ] > 0

    ):

        top_name, top_data = (
            top_products[0]
        )


        concentration = (

            top_data[
                "revenue"
            ]

            /

            snapshot[
                "total_revenue"
            ]

        ) * 100


        if concentration >= 60:

            risks.append(

                f"Revenue concentration "
                f"is high: "
                f"{top_name} contributes "
                f"{concentration:.1f}% "
                f"of recorded revenue."
            )


    if not risks:

        return (

            "No immediate high-priority "
            "risk was detected from the "
            "currently available "
            "business data."
        )


    return (

        "Current business risks:\n• "

        +

        "\n• ".join(
            risks
        )
    )


# =====================================================
# FORECAST
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


    model = forecast_data.get(

        "model_info",

        forecast_data.get(
            "model",
            {},
        ),
    )


    forecast_total = summary.get(

        "forecast_7_days",

        summary.get(
            "predicted_revenue",
            0,
        ),
    )


    predicted_orders = summary.get(

        "predicted_total_orders",

        0,
    )


    predicted_quantity = summary.get(

        "predicted_total_quantity",

        0,
    )


    method = model.get(

        "method",

        "Forecast model",
    )


    quality = model.get(

        "model_quality",

        "Not Available",
    )


    confidence = model.get(

        "confidence",

        "Not Available",
    )


    trend = model.get(

        "trend_direction",

        "Not Available",
    )


    answer = (

        f"Next 7-day forecast: "
        f"{money(forecast_total)} "
        f"predicted revenue, "
        f"about "
        f"{predicted_orders} "
        f"orders and "
        f"{predicted_quantity} "
        f"units. "

        f"Trend: "
        f"{trend}. "

        f"Method: "
        f"{method}. "

        f"Model quality: "
        f"{quality}. "

        f"Confidence: "
        f"{confidence}."
    )


    r2_score = model.get(
        "revenue_r2_score"
    )


    mae = model.get(
        "revenue_mae"
    )


    if r2_score is not None:

        answer += (

            f" R²: "
            f"{safe_float(r2_score):.4f}."
        )


    if mae is not None:

        answer += (

            f" MAE: "
            f"{money(mae)}."
        )


    if not model.get(
        "ml_ready",
        False,
    ):

        answer += (

            " The ML model is not "
            "fully ready, so fallback "
            "forecasting is being used."
        )


    elif (
        str(
            confidence
        ).lower()
        ==
        "low"
    ):

        answer += (

            " Confidence is low, "
            "so use the forecast "
            "as decision support "
            "rather than an exact result."
        )


    return answer


# =====================================================
# GEMINI FALLBACK
# =====================================================

def compact_ranking(
    grouped,
    metric="revenue",
    limit=8,
):

    rows = ranked(

        grouped,

        metric,

    )[:limit]


    return [

        {

            "name":
                str(
                    name
                ),

            "revenue":
                round(
                    safe_float(
                        data[
                            "revenue"
                        ]
                    ),
                    2,
                ),

            "quantity":
                safe_int(
                    data[
                        "quantity"
                    ]
                ),

            "orders":
                safe_int(
                    data[
                        "orders"
                    ]
                ),
        }

        for name, data
        in rows
    ]


def get_gemini_answer(
    question,
    user_details,
    snapshot,
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


    top_dates = [

        {

            "date":
                format_date(
                    sale_day
                ),

            "revenue":
                round(
                    data[
                        "revenue"
                    ],
                    2,
                ),

            "quantity":
                data[
                    "quantity"
                ],

            "orders":
                data[
                    "orders"
                ],
        }

        for sale_day, data
        in ranked(

            snapshot[
                "date_groups"
            ],

            "revenue",

        )[:7]
    ]


    context = {

        "total_revenue":
            round(
                snapshot[
                    "total_revenue"
                ],
                2,
            ),

        "total_sales":
            snapshot[
                "total_sales"
            ],

        "total_quantity":
            snapshot[
                "total_quantity"
            ],

        "average_order":
            round(
                snapshot[
                    "average_order"
                ],
                2,
            ),

        "total_customers":
            snapshot[
                "total_customers"
            ],

        "active_customers":
            snapshot[
                "active_customers"
            ],

        "inactive_customers":
            snapshot[
                "inactive_customers"
            ],

        "gst_total":
            round(
                snapshot[
                    "total_gst"
                ],
                2,
            ),

        "cgst_total":
            round(
                snapshot[
                    "total_cgst"
                ],
                2,
            ),

        "sgst_total":
            round(
                snapshot[
                    "total_sgst"
                ],
                2,
            ),

        "igst_total":
            round(
                snapshot[
                    "total_igst"
                ],
                2,
            ),

        "gst_invoice_count":
            len(
                snapshot[
                    "invoice_rows"
                ]
            ),

        "legacy_sale_count":
            len(
                snapshot[
                    "legacy_rows"
                ]
            ),

        "top_products":
            compact_ranking(

                snapshot[
                    "product_groups"
                ]
            ),

        "top_categories":
            compact_ranking(

                snapshot[
                    "category_groups"
                ]
            ),

        "top_customers":
            compact_ranking(

                snapshot[
                    "customer_groups"
                ]
            ),

        "top_sales_dates":
            top_dates,
    }


    prompt = f"""
You are Enterprise AI Business Copilot.

USER PROFILE

Name: {user_details["full_name"]}
Role: {user_details["role"]}

VERIFIED BUSINESS CONTEXT

{context}

STRICT RULES

1. Answer the user's exact question.
2. Never replace a specific question with a generic sales summary.
3. Never invent a business number.
4. Never invent a date.
5. Never invent a customer.
6. Never invent a product.
7. Never invent an invoice.
8. Never invent a GST value.
9. Never invent a profit or cost.
10. Never invent a forecast.
11. Use only VERIFIED BUSINESS CONTEXT for factual business numbers.
12. If the exact requested fact is not available, clearly say the current data is insufficient.
13. Distinguish revenue, quantity sold and order count.
14. Profit and margin cannot be calculated without cost or expense data.
15. Do not repeat totals unless those totals directly answer the user's question.
16. Keep the answer concise and useful.
17. Normally answer in 1 to 5 sentences.
18. If the user writes Tamil or Tanglish, reply in simple Tanglish.
19. Otherwise reply in the user's language.
20. Do not claim to browse the internet.

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


        if (

            response.text

            and

            response.text
            .strip()

        ):

            return (

                response.text
                .strip()
            )


    except Exception as error:

        print(

            "Gemini AI fallback error:",

            str(
                error
            ),
        )


    return None


# =====================================================
# MAIN UNIVERSAL BUSINESS ENGINE
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


    name = user_details[
        "full_name"
    ]


    snapshot = build_snapshot(
        db
    )


    # =================================================
    # BASIC CONVERSATION
    # =================================================

    if re.fullmatch(

        r"(hi|hello|hey|hai|hii|"
        r"hello there|hey there)"
        r"[!. ]*",

        q,
    ):

        return (

            f"Hi {name}! 👋 "
            f"How can I help with "
            f"your business today?"
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

            f"Your name is "
            f"{name}."
        )


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


    if contains_any(

        q,

        [
            "who are you",
            "what are you",
        ],
    ):

        return (

            "I'm Enterprise AI Business Copilot. "
            "I analyze sales, revenue, products, "
            "categories, customers, dates, invoices, "
            "GST, trends, ML forecasts, risks "
            "and recommendations using your "
            "business data."
        )


    if contains_any(

        q,

        [
            "what can you do",
            "how can you help",
            "show help",
        ],
    ):

        return (

            "I can answer totals, top/bottom "
            "performance, highest or lowest sales, "
            "best sales date/month, product/category/"
            "customer rankings, period comparisons, "
            "GST/invoices, customer status, ML forecasts, "
            "risks and recommendations."
        )


    if contains_any(

        q,

        [
            "how are you",
            "how r u",
        ],
    ):

        return (

            f"I'm doing well, "
            f"{name}! "
            f"I'm ready to analyze "
            f"your business data."
        )


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


    if re.fullmatch(

        r"(bye|goodbye|see you|see ya)"
        r"[!. ]*",

        q,
    ):

        return (

            f"Goodbye, "
            f"{name}! 👋"
        )


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
    # PROFIT / MARGIN
    # =================================================

    if contains_any(

        q,

        [
            "profit",
            "margin",
            "gross profit",
            "net profit",
            "cost of goods",
            "cogs",
        ],
    ):

        return (

            "Exact profit or margin cannot be "
            "calculated from the current data "
            "because product cost/expense data "
            "is not stored. I can accurately "
            "calculate recorded revenue, quantities, "
            "GST and order performance."
        )


    # =================================================
    # FORECAST
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
            "will sales",
            "expected sales",
        ],
    ):

        return build_forecast_answer(

            db,

            current_user,
        )


    # =================================================
    # INVOICE NUMBER LOOKUP
    # =================================================

    invoice_result = invoice_answer(

        snapshot,

        question,
    )


    if invoice_result:

        return invoice_result


    # =================================================
    # PERIOD COMPARISON
    # =================================================

    if contains_any(

        q,

        [
            "compare",
            "comparison",
            "versus",
            " vs ",
            "growth",
            "grew",
            "decline",
            "increased",
            "decreased",
        ],
    ):

        comparison = common_period_comparison(
            q
        )


        if comparison:

            return compare_periods(

                snapshot,

                comparison[0],

                comparison[1],
            )


    # =================================================
    # BEST / WORST DATE
    # =================================================

    if (

        contains_any(

            q,

            [
                "which date",
                "what date",
                "which day",
                "what day",
                "sales date",
                "best day",
                "highest day",
                "peak day",
            ],
        )

        and

        contains_any(

            q,

            [
                "high",
                "highest",
                "best",
                "most",
                "maximum",
                "max",
                "peak",
                "sales",
                "revenue",
            ],
        )

    ):

        if contains_any(

            q,

            [
                "units",
                "quantity",
                "sold the most",
            ],
        ):

            metric = "quantity"

        elif contains_any(

            q,

            [
                "orders",
                "order count",
            ],
        ):

            metric = "orders"

        else:

            metric = "revenue"


        return best_date_answer(

            snapshot,

            highest=True,

            metric=
                metric,
        )


    if (

        contains_any(

            q,

            [
                "which date",
                "what date",
                "which day",
                "what day",
                "worst day",
                "lowest day",
            ],
        )

        and

        contains_any(

            q,

            [
                "low",
                "lowest",
                "worst",
                "least",
                "minimum",
                "min",
            ],
        )

    ):

        if contains_any(

            q,

            [
                "units",
                "quantity",
                "sold the least",
            ],
        ):

            metric = "quantity"

        elif contains_any(

            q,

            [
                "orders",
                "order count",
            ],
        ):

            metric = "orders"

        else:

            metric = "revenue"


        return best_date_answer(

            snapshot,

            highest=False,

            metric=
                metric,
        )


    # =================================================
    # BEST / WORST MONTH
    # =================================================

    if (

        contains_any(

            q,

            [
                "which month",
                "what month",
                "best month",
                "highest month",
                "peak month",
            ],
        )

        and

        contains_any(

            q,

            [
                "high",
                "highest",
                "best",
                "most",
                "maximum",
                "sales",
                "revenue",
                "peak",
            ],
        )

    ):

        if contains_any(

            q,

            [
                "units",
                "quantity",
                "sold the most",
            ],
        ):

            metric = "quantity"

        elif contains_any(

            q,

            [
                "orders",
                "order count",
            ],
        ):

            metric = "orders"

        else:

            metric = "revenue"


        return best_month_answer(

            snapshot,

            highest=True,

            metric=
                metric,
        )


    if (

        contains_any(

            q,

            [
                "which month",
                "what month",
                "worst month",
                "lowest month",
            ],
        )

        and

        contains_any(

            q,

            [
                "low",
                "lowest",
                "worst",
                "least",
                "minimum",
            ],
        )

    ):

        if contains_any(

            q,

            [
                "units",
                "quantity",
                "sold the least",
            ],
        ):

            metric = "quantity"

        elif contains_any(

            q,

            [
                "orders",
                "order count",
            ],
        ):

            metric = "orders"

        else:

            metric = "revenue"


        return best_month_answer(

            snapshot,

            highest=False,

            metric=
                metric,
        )


    # =================================================
    # HIGHEST SINGLE SALE
    # =================================================

    if contains_any(

        q,

        [
            "highest sale",
            "largest sale",
            "biggest sale",
            "best sale",
            "best sales",
            "highest order",
            "largest order",
            "biggest order",
            "highest order amount",
            "maximum sale",
            "max sale",
        ],
    ):

        if not snapshot[
            "sales"
        ]:

            return (

                "There are no "
                "sales records yet."
            )


        highest_sale = max(

            snapshot[
                "sales"
            ],

            key=
                sale_amount,
        )


        return (

            f"The highest single sale is "
            f"{money(sale_amount(highest_sale))} "
            f"for "
            f"{clean_name(getattr(highest_sale, 'product_name', None))}, "
            f"quantity "
            f"{sale_quantity(highest_sale)}, "
            f"customer "
            f"{clean_name(getattr(highest_sale, 'customer_name', None), 'N/A')}, "
            f"on "
            f"{format_date(sale_date_value(highest_sale))}."
        )


    # =================================================
    # LOWEST SINGLE SALE
    # =================================================

    if contains_any(

        q,

        [
            "lowest sale",
            "smallest sale",
            "lowest order",
            "smallest order",
            "minimum sale",
            "min sale",
        ],
    ):

        if not snapshot[
            "sales"
        ]:

            return (

                "There are no "
                "sales records yet."
            )


        lowest_sale = min(

            snapshot[
                "sales"
            ],

            key=
                sale_amount,
        )


        return (

            f"The lowest single sale is "
            f"{money(sale_amount(lowest_sale))} "
            f"for "
            f"{clean_name(getattr(lowest_sale, 'product_name', None))}, "
            f"quantity "
            f"{sale_quantity(lowest_sale)}, "
            f"on "
            f"{format_date(sale_date_value(lowest_sale))}."
        )


    # =================================================
    # PRODUCT MATCH / COMPARISON
    # =================================================

    product_names = list(

        snapshot[
            "product_groups"
        ].keys()
    )


    matched_products = matched_entities(

        q,

        product_names,
    )


    product_comparison = contains_any(

        q,

        [
            "compare",
            " vs ",
            "versus",
            "better",
            "which is best",
            "which is better",
        ],
    )


    if (

        matched_products

        and

        not product_comparison

    ):

        matched_products = (
            matched_products[:1]
        )


    if (

        len(
            matched_products
        ) >= 2

        and

        product_comparison

    ):

        result = compare_entities(

            snapshot[
                "product_groups"
            ],

            matched_products[:2],

            "Product",
        )


        if result:

            return result


    if (

        len(
            matched_products
        ) == 1

        and

        contains_any(

            q,

            [
                "product",
                "sale",
                "sales",
                "revenue",
                "sold",
                "order",
                "orders",
                "quantity",
                "performance",
                "how much",
                "how many",
            ],
        )

    ):

        product_name = (
            matched_products[0]
        )


        return specific_group_answer(

            product_name,

            snapshot[
                "product_groups"
            ][
                product_name
            ],

            "Product",
        )


    # =================================================
    # PRODUCT RANKINGS
    # =================================================

    if contains_any(

        q,

        [
            "top 5 products",
            "top five products",
            "top products",
            "best products",
        ],
    ):

        if contains_any(

            q,

            [
                "selling",
                "sold",
                "quantity",
                "units",
            ],
        ):

            metric = "quantity"

        else:

            metric = "revenue"


        return top_n_answer(

            snapshot[
                "product_groups"
            ],

            "Products",

            metric,

            n=5,

            highest=True,
        )


    if contains_any(

        q,

        [
            "bottom products",
            "worst products",
            "lowest products",
            "least products",
        ],
    ):

        if contains_any(

            q,

            [
                "selling",
                "sold",
                "quantity",
                "units",
            ],
        ):

            metric = "quantity"

        else:

            metric = "revenue"


        return top_n_answer(

            snapshot[
                "product_groups"
            ],

            "Products",

            metric,

            n=5,

            highest=False,
        )


    if contains_any(

        q,

        [
            "best selling product",
            "best-selling product",
            "highest selling product",
            "most sold product",
            "most units",
            "which product sold the most",
            "top selling product",
        ],
    ):

        return rank_answer(

            snapshot[
                "product_groups"
            ],

            "Product",

            "quantity",

            highest=True,
        )


    if contains_any(

        q,

        [
            "least selling product",
            "lowest selling product",
            "least sold product",
            "which product sold the least",
            "worst selling product",
        ],
    ):

        return rank_answer(

            snapshot[
                "product_groups"
            ],

            "Product",

            "quantity",

            highest=False,
        )


    if contains_any(

        q,

        [
            "top product",
            "best product",
            "highest revenue product",
            "most revenue product",
            "which product generated the most revenue",
            "which product generated most revenue",
            "which product has highest revenue",
            "product with highest revenue",
        ],
    ):

        return rank_answer(

            snapshot[
                "product_groups"
            ],

            "Product",

            "revenue",

            highest=True,
        )


    if contains_any(

        q,

        [
            "lowest revenue product",
            "least revenue product",
            "worst product",
            "product with lowest revenue",
        ],
    ):

        return rank_answer(

            snapshot[
                "product_groups"
            ],

            "Product",

            "revenue",

            highest=False,
        )


    if contains_any(

        q,

        [
            "which product should i focus on",
            "what product should i focus on",
            "product should i focus on",
            "focus product",
            "which product should i promote",
            "which product should i market",
        ],
    ):

        rows = ranked(

            snapshot[
                "product_groups"
            ],

            "revenue",
        )


        if not rows:

            return (

                "There are no sales records yet, "
                "so I cannot recommend a "
                "focus product."
            )


        product_name, data = (
            rows[0]
        )


        return (

            f"Focus on "
            f"{product_name}. "
            f"It currently leads product revenue "
            f"with "
            f"{money(data['revenue'])}, "
            f"{safe_int(data['quantity'])} units "
            f"and "
            f"{safe_int(data['orders'])} orders."
        )


    # =================================================
    # CATEGORY MATCH / COMPARISON
    # =================================================

    category_names = list(

        snapshot[
            "category_groups"
        ].keys()
    )


    matched_categories = matched_entities(

        q,

        category_names,
    )


    category_comparison = contains_any(

        q,

        [
            "compare",
            " vs ",
            "versus",
            "better",
            "which is better",
        ],
    )


    if (

        matched_categories

        and

        not category_comparison

    ):

        matched_categories = (
            matched_categories[:1]
        )


    if (

        len(
            matched_categories
        ) >= 2

        and

        category_comparison

    ):

        result = compare_entities(

            snapshot[
                "category_groups"
            ],

            matched_categories[:2],

            "Category",
        )


        if result:

            return result


    if (

        len(
            matched_categories
        ) == 1

        and

        contains_any(

            q,

            [
                "category",
                "revenue",
                "sales",
                "sold",
                "quantity",
                "orders",
                "performance",
            ],
        )

    ):

        category_name = (
            matched_categories[0]
        )


        return specific_group_answer(

            category_name,

            snapshot[
                "category_groups"
            ][
                category_name
            ],

            "Category",
        )


    if contains_any(

        q,

        [
            "top categories",
            "best categories",
            "top 5 categories",
            "top five categories",
        ],
    ):

        metric = (

            "quantity"

            if contains_any(

                q,

                [
                    "selling",
                    "sold",
                    "quantity",
                    "units",
                ],
            )

            else "revenue"
        )


        return top_n_answer(

            snapshot[
                "category_groups"
            ],

            "Categories",

            metric,

            n=5,

            highest=True,
        )


    if contains_any(

        q,

        [
            "best selling category",
            "highest selling category",
            "most sold category",
            "top selling category",
        ],
    ):

        return rank_answer(

            snapshot[
                "category_groups"
            ],

            "Category",

            "quantity",

            highest=True,
        )


    if contains_any(

        q,

        [
            "least selling category",
            "lowest selling category",
            "worst selling category",
        ],
    ):

        return rank_answer(

            snapshot[
                "category_groups"
            ],

            "Category",

            "quantity",

            highest=False,
        )


    if contains_any(

        q,

        [
            "top category",
            "best category",
            "highest revenue category",
            "strongest category",
        ],
    ):

        return rank_answer(

            snapshot[
                "category_groups"
            ],

            "Category",

            "revenue",

            highest=True,
        )


    if contains_any(

        q,

        [
            "lowest category",
            "worst category",
            "weakest category",
        ],
    ):

        return rank_answer(

            snapshot[
                "category_groups"
            ],

            "Category",

            "revenue",

            highest=False,
        )


    if contains_any(

        q,

        [
            "which category should i focus on",
            "focus category",
            "category to focus on",
        ],
    ):

        rows = ranked(

            snapshot[
                "category_groups"
            ],

            "revenue",
        )


        if not rows:

            return (

                "There are no categorized "
                "sales records yet."
            )


        category_name, data = (
            rows[0]
        )


        return (

            f"Focus on "
            f"{category_name}; "
            f"it currently leads "
            f"category revenue with "
            f"{money(data['revenue'])}."
        )


    # =================================================
    # CUSTOMER MATCH / COMPARISON
    # =================================================

    customer_names = list(

        snapshot[
            "customer_groups"
        ].keys()
    )


    matched_customers = matched_entities(

        q,

        customer_names,
    )


    customer_comparison = contains_any(

        q,

        [
            "compare",
            " vs ",
            "versus",
            "better",
            "bought more",
            "purchased more",
        ],
    )


    if (

        matched_customers

        and

        not customer_comparison

    ):

        matched_customers = (
            matched_customers[:1]
        )


    if (

        len(
            matched_customers
        ) >= 2

        and

        customer_comparison

    ):

        result = compare_entities(

            snapshot[
                "customer_groups"
            ],

            matched_customers[:2],

            "Customer",
        )


        if result:

            return result


    if (

        len(
            matched_customers
        ) == 1

        and

        contains_any(

            q,

            [
                "customer",
                "client",
                "purchase",
                "purchased",
                "bought",
                "revenue",
                "sales",
                "orders",
                "units",
            ],
        )

    ):

        customer_name = (
            matched_customers[0]
        )


        return specific_group_answer(

            customer_name,

            snapshot[
                "customer_groups"
            ][
                customer_name
            ],

            "Customer",
        )


    # =================================================
    # CUSTOMER RANKINGS
    # =================================================

    if contains_any(

        q,

        [
            "top customers",
            "best customers",
            "top 5 customers",
            "top five customers",
        ],
    ):

        if contains_any(

            q,

            [
                "units",
                "quantity",
                "purchased",
                "bought",
            ],
        ):

            metric = "quantity"

        elif contains_any(

            q,

            [
                "orders",
                "frequent",
            ],
        ):

            metric = "orders"

        else:

            metric = "revenue"


        return top_n_answer(

            snapshot[
                "customer_groups"
            ],

            "Customers",

            metric,

            n=5,

            highest=True,
        )


    if contains_any(

        q,

        [
            "top customer",
            "best customer",
            "highest value customer",
            "highest revenue customer",
            "customer spent the most",
            "who spent the most",
            "biggest customer",
        ],
    ):

        if contains_any(

            q,

            [
                "units",
                "quantity",
                "purchased",
                "bought",
            ],
        ):

            metric = "quantity"

        elif contains_any(

            q,

            [
                "orders",
                "frequent",
            ],
        ):

            metric = "orders"

        else:

            metric = "revenue"


        return rank_answer(

            snapshot[
                "customer_groups"
            ],

            "Customer",

            metric,

            highest=True,
        )


    if contains_any(

        q,

        [
            "customer purchased the most",
            "customer bought the most",
            "most units customer",
            "which customer purchased the most",
            "which customer bought the most",
        ],
    ):

        return rank_answer(

            snapshot[
                "customer_groups"
            ],

            "Customer",

            "quantity",

            highest=True,
        )


    if contains_any(

        q,

        [
            "most orders customer",
            "customer with most orders",
            "frequent customer",
            "most frequent customer",
        ],
    ):

        return rank_answer(

            snapshot[
                "customer_groups"
            ],

            "Customer",

            "orders",

            highest=True,
        )


    if contains_any(

        q,

        [
            "lowest value customer",
            "lowest revenue customer",
            "least customer",
        ],
    ):

        return rank_answer(

            snapshot[
                "customer_groups"
            ],

            "Customer",

            "revenue",

            highest=False,
        )


    # =================================================
    # CUSTOMER STATUS
    # =================================================

    if contains_any(

        q,

        [
            "list inactive customers",
            "show inactive customers",
            "who are inactive customers",
        ],
    ):

        return customer_status_answer(

            snapshot,

            "inactive",

            list_names=True,
        )


    if contains_any(

        q,

        [
            "list active customers",
            "show active customers",
            "who are active customers",
        ],
    ):

        return customer_status_answer(

            snapshot,

            "active",

            list_names=True,
        )


    if contains_any(

        q,

        [
            "inactive customer",
            "inactive customers",
        ],
    ):

        return customer_status_answer(

            snapshot,

            "inactive",
        )


    if contains_any(

        q,

        [
            "active customer",
            "active customers",
        ],
    ):

        return customer_status_answer(

            snapshot,

            "active",
        )


    if contains_any(

        q,

        [
            "new customer",
            "new customers",
            "customers added",
            "customers joined",
        ],
    ):

        customer_period = resolve_period(
            question
        )


        if customer_period:

            return new_customer_period_answer(

                snapshot,

                customer_period,
            )


    if contains_any(

        q,

        [
            "how many customers",
            "total customers",
            "customer count",
            "number of customers",
        ],
    ):

        return (

            f"You have "
            f"{snapshot['total_customers']} "
            f"registered customers: "

            f"{snapshot['active_customers']} "
            f"active and "

            f"{snapshot['inactive_customers']} "
            f"inactive."
        )


    # =================================================
    # HSN
    # =================================================

    if contains_any(

        q,

        [
            "top hsn",
            "best hsn",
            "highest hsn",
        ],
    ):

        return rank_answer(

            snapshot[
                "hsn_groups"
            ],

            "HSN code",

            "revenue",

            highest=True,
        )


    # =================================================
    # TAXABLE AMOUNT
    # =================================================

    if contains_any(

        q,

        [
            "total taxable amount",
            "taxable amount total",
            "taxable revenue",
        ],
    ):

        known_taxable = sum(

            safe_float(

                getattr(
                    sale,
                    "taxable_amount",
                    0,
                )
            )

            for sale
            in snapshot[
                "invoice_rows"
            ]
        )


        return (

            f"Known taxable amount from "
            f"GST/invoice sales is "
            f"{money(known_taxable)}. "

            f"This excludes "
            f"{len(snapshot['legacy_rows'])} "
            f"legacy sale(s) that do not "
            f"have taxable/GST fields."
        )


    # =================================================
    # INVOICE COUNT
    # =================================================

    if contains_any(

        q,

        [
            "how many invoices",
            "invoice count",
            "total invoices",
            "number of invoices",
        ],
    ):

        return (

            f"There are "
            f"{len(snapshot['invoice_rows'])} "
            f"generated GST invoice(s) and "

            f"{len(snapshot['legacy_rows'])} "
            f"legacy sale(s) without "
            f"invoice numbers."
        )


    if contains_any(

        q,

        [
            "highest invoice",
            "largest invoice",
            "biggest invoice",
            "highest invoice amount",
        ],
    ):

        if not snapshot[
            "invoice_rows"
        ]:

            return (

                "There are no "
                "generated invoices yet."
            )


        highest_invoice = max(

            snapshot[
                "invoice_rows"
            ],

            key=
                sale_amount,
        )


        return (

            f"The highest invoice is "
            f"{getattr(highest_invoice, 'invoice_number', 'N/A')} "
            f"at "
            f"{money(sale_amount(highest_invoice))} "
            f"for "
            f"{clean_name(getattr(highest_invoice, 'product_name', None))}, "
            f"dated "
            f"{format_date(sale_date_value(highest_invoice))}."
        )


    # =================================================
    # GST / TAX
    # =================================================

    gst_result = gst_answer(

        snapshot,

        question,
    )


    if gst_result:

        return gst_result


    # =================================================
    # EXACT / RELATIVE PERIOD
    # =================================================

    period = resolve_period(
        question
    )


    if (

        period

        and

        has_business_word(
            q
        )

    ):

        (
            start_date,
            end_date,
            label,
        ) = period


        period_rows = rows_in_period(

            snapshot[
                "sales"
            ],

            start_date,

            end_date,
        )


        return sale_period_summary(

            period_rows,

            label,
        )


    # =================================================
    # GROUPED BREAKDOWNS
    # =================================================

    if contains_any(

        q,

        [
            "product wise sales",
            "product-wise sales",
            "sales by product",
            "product breakdown",
        ],
    ):

        return top_n_answer(

            snapshot[
                "product_groups"
            ],

            "Products",

            "revenue",

            n=10,

            highest=True,
        )


    if contains_any(

        q,

        [
            "category wise sales",
            "category-wise sales",
            "sales by category",
            "category breakdown",
        ],
    ):

        return top_n_answer(

            snapshot[
                "category_groups"
            ],

            "Categories",

            "revenue",

            n=10,

            highest=True,
        )


    if contains_any(

        q,

        [
            "customer wise sales",
            "customer-wise sales",
            "sales by customer",
            "customer breakdown",
        ],
    ):

        return top_n_answer(

            snapshot[
                "customer_groups"
            ],

            "Customers",

            "revenue",

            n=10,

            highest=True,
        )


    if contains_any(

        q,

        [
            "date wise sales",
            "date-wise sales",
            "daily sales",
            "sales by date",
        ],
    ):

        rows = ranked(

            snapshot[
                "date_groups"
            ],

            "revenue",

        )[:10]


        if not rows:

            return (

                "There are no dated "
                "sales records yet."
            )


        lines = [

            "Top sales dates "
            "by revenue:"
        ]


        for index, (
            sale_day,
            data,
        ) in enumerate(

            rows,

            start=1,
        ):

            lines.append(

                f"{index}. "
                f"{format_date(sale_day)} "
                f"— "
                f"{money(data['revenue'])}, "
                f"{safe_int(data['orders'])} "
                f"orders, "
                f"{safe_int(data['quantity'])} "
                f"units"
            )


        return "\n".join(
            lines
        )


    if contains_any(

        q,

        [
            "month wise sales",
            "month-wise sales",
            "monthly sales",
            "sales by month",
        ],
    ):

        rows = ranked(

            snapshot[
                "month_groups"
            ],

            "revenue",

        )[:12]


        if not rows:

            return (

                "There are no dated "
                "sales records yet."
            )


        lines = [

            "Monthly sales "
            "by revenue:"
        ]


        for index, (
            month_key,
            data,
        ) in enumerate(

            rows,

            start=1,
        ):

            month_label = (

                datetime.strptime(

                    month_key,

                    "%Y-%m",

                ).strftime(
                    "%B %Y"
                )
            )


            lines.append(

                f"{index}. "
                f"{month_label} "
                f"— "
                f"{money(data['revenue'])}, "
                f"{safe_int(data['orders'])} "
                f"orders, "
                f"{safe_int(data['quantity'])} "
                f"units"
            )


        return "\n".join(
            lines
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
            "latest sale",
        ],
    ):

        recent_rows = sorted(

            snapshot[
                "sales"
            ],

            key=lambda sale:
                (
                    sale_date_value(
                        sale
                    )
                    or datetime.min
                ),

            reverse=True,

        )[:5]


        if not recent_rows:

            return (

                "There are no "
                "sales records yet."
            )


        lines = [

            "Latest sales:"
        ]


        for sale in recent_rows:

            invoice_number = (

                getattr(
                    sale,
                    "invoice_number",
                    None,
                )

                or "Legacy"
            )


            lines.append(

                f"• "
                f"{invoice_number} "
                f"— "
                f"{clean_name(getattr(sale, 'product_name', None))} "
                f"— "
                f"{money(sale_amount(sale))} "
                f"— "
                f"{format_date(sale_date_value(sale))}"
            )


        return "\n".join(
            lines
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

            f"Average order value is "
            f"{money(snapshot['average_order'])}, "
            f"based on "
            f"{snapshot['total_sales']} "
            f"sales/orders."
        )


    # =================================================
    # TOTAL QUANTITY
    # =================================================

    if contains_any(

        q,

        [
            "total quantity",
            "units sold",
            "how many units",
            "quantity sold",
        ],
    ):

        return (

            f"Total quantity sold is "
            f"{snapshot['total_quantity']} "
            f"units across "
            f"{snapshot['total_sales']} "
            f"sales/orders."
        )


    # =================================================
    # TOTAL SALES / ORDERS
    # =================================================

    if contains_any(

        q,

        [
            "how many sales",
            "sales count",
            "total sales",
            "how many orders",
            "order count",
            "total orders",
        ],
    ):

        return (

            f"You currently have "
            f"{snapshot['total_sales']} "
            f"sales/orders."
        )


    # =================================================
    # TOTAL REVENUE
    # =================================================

    if contains_any(

        q,

        [
            "total revenue",
            "business revenue",
            "overall revenue",
            "total income",
            "total turnover",
        ],
    ):

        return (

            f"Total recorded business "
            f"revenue is "
            f"{money(snapshot['total_revenue'])}."
        )


    # =================================================
    # GROWTH / TREND
    # =================================================

    if contains_any(

        q,

        [
            "sales growth",
            "revenue growth",
            "business growth",
            "performance trend",
            "revenue trend",
        ],
    ):

        return growth_snapshot(
            snapshot
        )


    # =================================================
    # RECOMMENDATION
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
            "business advice",
        ],
    ):

        return build_recommendation(
            snapshot
        )


    # =================================================
    # RISK
    # =================================================

    if contains_any(

        q,

        [
            "risk",
            "risks",
            "business risk",
            "warning",
            "business problem",
        ],
    ):

        return build_risk_answer(
            snapshot
        )


    # =================================================
    # BUSINESS HEALTH
    # =================================================

    if contains_any(

        q,

        [
            "business health",
            "health of business",
            "how is my business doing",
            "business performance",
        ],
    ):

        return (

            f"Business health snapshot: "
            f"{money(snapshot['total_revenue'])} "
            f"revenue from "
            f"{snapshot['total_sales']} orders, "
            f"{snapshot['total_quantity']} units sold, "
            f"{snapshot['active_customers']} active customers "
            f"and "
            f"{snapshot['inactive_customers']} inactive customers. "

            f"{growth_snapshot(snapshot)}"
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

        top_product_rows = ranked(

            snapshot[
                "product_groups"
            ],

            "revenue",

        )[:1]


        top_category_rows = ranked(

            snapshot[
                "category_groups"
            ],

            "revenue",

        )[:1]


        top_product_text = (

            top_product_rows[0][0]

            if top_product_rows

            else "N/A"
        )


        top_category_text = (

            top_category_rows[0][0]

            if top_category_rows

            else "N/A"
        )


        return (

            "Current business summary:\n"

            f"• Revenue: "
            f"{money(snapshot['total_revenue'])}\n"

            f"• Sales/Orders: "
            f"{snapshot['total_sales']}\n"

            f"• Quantity sold: "
            f"{snapshot['total_quantity']}\n"

            f"• Customers: "
            f"{snapshot['total_customers']}\n"

            f"• Average order value: "
            f"{money(snapshot['average_order'])}\n"

            f"• Top product by revenue: "
            f"{top_product_text}\n"

            f"• Top category by revenue: "
            f"{top_category_text}\n"

            f"• Recorded GST: "
            f"{money(snapshot['total_gst'])}"
        )


    # =================================================
    # VERY GENERIC REVENUE
    # ONLY EXACT SHORT QUESTIONS
    # =================================================

    if q in {

        "revenue",

        "income",

        "turnover",
    }:

        return (

            f"Total recorded business "
            f"revenue is "
            f"{money(snapshot['total_revenue'])}."
        )


    # =================================================
    # VERY GENERIC SALES
    # ONLY EXACT SHORT QUESTIONS
    # =================================================

    if q in {

        "sales",

        "orders",

        "sales status",

        "order status",
    }:

        return (

            f"You currently have "
            f"{snapshot['total_sales']} "
            f"sales/orders, "
            f"{snapshot['total_quantity']} "
            f"units sold and "
            f"{money(snapshot['total_revenue'])} "
            f"recorded revenue."
        )


    # =================================================
    # GEMINI FALLBACK
    # =================================================

    gemini_answer = get_gemini_answer(

        question,

        user_details,

        snapshot,
    )


    if gemini_answer:

        return gemini_answer


    # =================================================
    # SAFE LOCAL FALLBACK
    # =================================================

    if has_business_word(
        q
    ):

        return (

            "I understood this as a business "
            "question, but I do not have enough "
            "verified data or a matching metric "
            "to answer it exactly. "

            "Please mention the metric you want, "
            "such as revenue, quantity, orders, "
            "product, customer, date, GST, invoice, "
            "forecast, risk or recommendation."
        )


    return (

        "I can help with your business data "
        "and general business questions. "
        "Ask me about sales, revenue, products, "
        "customers, GST, invoices, trends "
        "or forecasts."
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


    try:

        answer = build_business_answer(

            message,

            db,

            current_user,
        )


    except HTTPException:

        raise


    except Exception as error:

        print(

            "AI Copilot error:",

            str(
                error
            ),
        )


        raise HTTPException(

            status_code=500,

            detail=
                "AI Copilot could not process "
                "this request right now.",
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

        "engine":
            "universal_business_copilot_v2",
    }