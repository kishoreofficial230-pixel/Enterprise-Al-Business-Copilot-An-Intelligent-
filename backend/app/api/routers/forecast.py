from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from datetime import datetime, date, timedelta
import math

from sklearn.linear_model import LinearRegression

from app.database.database import get_db
from app.core.security import get_current_user
from app.models.sales import Sale


router = APIRouter(
    prefix="/forecast",
    tags=["Sales Forecast"],
)


# =====================================================
# FORECAST SETTINGS
# =====================================================

FORECAST_DAYS = 7

MINIMUM_ML_DAYS = 5


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def to_date(value):

    if value is None:
        return None

    if isinstance(
        value,
        datetime
    ):
        return value.date()

    if isinstance(
        value,
        date
    ):
        return value

    return datetime.strptime(
        str(value),
        "%Y-%m-%d"
    ).date()


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


def get_model_quality(
    r2_score
):

    if r2_score is None:

        return "Not Available"

    if not math.isfinite(
        r2_score
    ):

        return "Not Available"

    if r2_score >= 0.85:

        return "Excellent"

    if r2_score >= 0.70:

        return "Good"

    if r2_score >= 0.50:

        return "Moderate"

    if r2_score >= 0.30:

        return "Weak"

    return "Very Weak"


# =====================================================
# SALES FORECAST API
# =====================================================

@router.get("/sales")
def sales_forecast(
    db: Session = Depends(
        get_db
    ),
    current_user: dict = Depends(
        get_current_user
    ),
):


    # =====================================================
    # FETCH DAILY SALES FROM MYSQL
    # =====================================================

    daily_sales_query = (
        db.query(

            func.date(
                Sale.sale_date
            ).label(
                "sale_day"
            ),

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
            Sale.sale_date.isnot(
                None
            )
        )
        .group_by(
            func.date(
                Sale.sale_date
            )
        )
        .order_by(
            func.date(
                Sale.sale_date
            )
        )
        .all()
    )


    # =====================================================
    # NO SALES DATA
    # =====================================================

    if not daily_sales_query:

        return {

            "message":
                "No sales data available",

            "historical": [],

            "forecast": [],

            "summary": {

                "historical_revenue":
                    0,

                "historical_days":
                    0,

                "average_daily_revenue":
                    0,

                "forecast_7_days":
                    0,

                "predicted_average_daily_revenue":
                    0,

                "average_daily_orders":
                    0,

                "average_daily_quantity":
                    0,

                "average_order_value":
                    0,

                "average_units_per_order":
                    0,
            },

            "model_info": {

                "method":
                    "No Data",

                "ml_ready":
                    False,

                "training_days":
                    0,

                "minimum_ml_days":
                    MINIMUM_ML_DAYS,

                "revenue_r2_score":
                    None,

                "model_quality":
                    "Not Available",

                "revenue_trend_per_day":
                    0,

                "trend_direction":
                    "No Data",

                "forecast_start_date":
                    None,
            },

            "insight":
                "More sales data is required "
                "to generate a forecast.",

            "user_id":
                current_user.get(
                    "sub"
                ),
        }


    # =====================================================
    # CONVERT MYSQL RESULT TO DICTIONARY
    # =====================================================

    raw_daily_data = {}


    for row in daily_sales_query:

        sale_day = to_date(
            row.sale_day
        )


        if sale_day is None:

            continue


        raw_daily_data[
            sale_day
        ] = {

            "revenue":
                safe_float(
                    row.revenue
                ),

            "orders":
                safe_int(
                    row.orders
                ),

            "quantity":
                safe_int(
                    row.quantity
                ),
        }


    # =====================================================
    # CHECK VALID DATA
    # =====================================================

    if not raw_daily_data:

        return {

            "message":
                "No valid dated sales records found",

            "historical": [],

            "forecast": [],

            "summary": {

                "historical_revenue":
                    0,

                "historical_days":
                    0,

                "average_daily_revenue":
                    0,

                "forecast_7_days":
                    0,

                "predicted_average_daily_revenue":
                    0,

                "average_daily_orders":
                    0,

                "average_daily_quantity":
                    0,

                "average_order_value":
                    0,

                "average_units_per_order":
                    0,
            },

            "model_info": {

                "method":
                    "No Data",

                "ml_ready":
                    False,

                "training_days":
                    0,

                "minimum_ml_days":
                    MINIMUM_ML_DAYS,

                "revenue_r2_score":
                    None,

                "model_quality":
                    "Not Available",

                "revenue_trend_per_day":
                    0,

                "trend_direction":
                    "No Data",

                "forecast_start_date":
                    None,
            },

            "insight":
                "No valid dated sales "
                "records were found.",

            "user_id":
                current_user.get(
                    "sub"
                ),
        }


    # =====================================================
    # FIRST AND LAST SALES DATE
    # =====================================================

    first_day = min(
        raw_daily_data.keys()
    )


    last_day = max(
        raw_daily_data.keys()
    )


    # =====================================================
    # BUILD CONTINUOUS DAILY HISTORY
    # =====================================================

    daily_data = []


    current_day = first_day


    while (
        current_day <=
        last_day
    ):

        values = raw_daily_data.get(
            current_day,
            {
                "revenue":
                    0.0,

                "orders":
                    0,

                "quantity":
                    0,
            }
        )


        daily_data.append({

            "date":
                current_day,

            "revenue":
                safe_float(
                    values[
                        "revenue"
                    ]
                ),

            "orders":
                safe_int(
                    values[
                        "orders"
                    ]
                ),

            "quantity":
                safe_int(
                    values[
                        "quantity"
                    ]
                ),
        })


        current_day += timedelta(
            days=1
        )


    # =====================================================
    # HISTORICAL RESPONSE
    # =====================================================

    historical = []


    for item in daily_data:

        historical.append({

            "date":
                str(
                    item[
                        "date"
                    ]
                ),

            "revenue":
                round(
                    item[
                        "revenue"
                    ],
                    2
                ),

            "orders":
                item[
                    "orders"
                ],

            "quantity":
                item[
                    "quantity"
                ],
        })


    # =====================================================
    # HISTORICAL VALUES
    # =====================================================

    revenues = [

        item[
            "revenue"
        ]

        for item
        in daily_data
    ]


    orders = [

        item[
            "orders"
        ]

        for item
        in daily_data
    ]


    quantities = [

        item[
            "quantity"
        ]

        for item
        in daily_data
    ]


    # =====================================================
    # COUNTS
    # =====================================================

    actual_sales_days = len(
        raw_daily_data
    )


    calendar_training_days = len(
        daily_data
    )


    # =====================================================
    # TOTALS
    # =====================================================

    total_revenue = sum(
        revenues
    )


    total_orders = sum(
        orders
    )


    total_quantity = sum(
        quantities
    )


    # =====================================================
    # HISTORICAL AVERAGES
    # =====================================================

    average_daily_revenue = (

        total_revenue /
        calendar_training_days

        if calendar_training_days

        else 0
    )


    average_daily_orders = (

        total_orders /
        calendar_training_days

        if calendar_training_days

        else 0
    )


    average_daily_quantity = (

        total_quantity /
        calendar_training_days

        if calendar_training_days

        else 0
    )


    average_order_value = (

        total_revenue /
        total_orders

        if total_orders

        else 0
    )


    average_units_per_order = (

        total_quantity /
        total_orders

        if total_orders

        else 0
    )


    # =====================================================
    # ML READINESS
    # =====================================================

    ml_ready = (

        actual_sales_days >=
        MINIMUM_ML_DAYS
    )


    # =====================================================
    # FORECAST START DATE
    # =====================================================

    today = date.today()


    tomorrow = (
        today +
        timedelta(
            days=1
        )
    )


    day_after_last_sale = (
        last_day +
        timedelta(
            days=1
        )
    )


    forecast_start_date = max(
        tomorrow,
        day_after_last_sale
    )


    # =====================================================
    # MODEL DEFAULT VALUES
    # =====================================================

    forecast = []


    revenue_r2_score = None


    revenue_trend_per_day = 0.0


    trend_direction = (
        "Stable"
    )


    model_quality = (
        "Not Available"
    )


    # =====================================================
    # MACHINE LEARNING MODE
    # =====================================================

    if ml_ready:


        # =================================================
        # DATE INDEX FEATURES
        # =================================================

        X = []


        for item in daily_data:

            day_index = (
                item[
                    "date"
                ] -
                first_day
            ).days


            X.append([
                day_index
            ])


        # =================================================
        # TRAIN REVENUE MODEL
        # =================================================

        revenue_model = (
            LinearRegression()
        )


        revenue_model.fit(
            X,
            revenues
        )


        # =================================================
        # MODEL R2 SCORE
        # =================================================

        revenue_r2_score = float(
            revenue_model.score(
                X,
                revenues
            )
        )


        if not math.isfinite(
            revenue_r2_score
        ):

            revenue_r2_score = None


        # =================================================
        # MODEL QUALITY
        # =================================================

        model_quality = (
            get_model_quality(
                revenue_r2_score
            )
        )


        # =================================================
        # REVENUE TREND
        # =================================================

        revenue_trend_per_day = float(
            revenue_model.coef_[
                0
            ]
        )


        if (
            revenue_trend_per_day >
            0.01
        ):

            trend_direction = (
                "Increasing"
            )


        elif (
            revenue_trend_per_day <
            -0.01
        ):

            trend_direction = (
                "Decreasing"
            )


        else:

            trend_direction = (
                "Stable"
            )


        # =================================================
        # NEXT 7 DAYS FORECAST
        # =================================================

        for day_number in range(
            FORECAST_DAYS
        ):

            forecast_date = (
                forecast_start_date +
                timedelta(
                    days=day_number
                )
            )


            future_index = (
                forecast_date -
                first_day
            ).days


            # =============================================
            # ML REVENUE PREDICTION
            # =============================================

            predicted_revenue = float(
                revenue_model.predict(
                    [
                        [
                            future_index
                        ]
                    ]
                )[
                    0
                ]
            )


            predicted_revenue = max(
                predicted_revenue,
                0
            )


            # =============================================
            # SENSIBLE ORDER PREDICTION
            # =============================================

            if (
                predicted_revenue > 0
                and
                average_order_value > 0
            ):

                predicted_orders = round(
                    predicted_revenue /
                    average_order_value
                )


                predicted_orders = max(
                    predicted_orders,
                    1
                )


            else:

                predicted_orders = 0


            # =============================================
            # SENSIBLE QUANTITY PREDICTION
            # =============================================

            if (
                predicted_orders > 0
                and
                average_units_per_order > 0
            ):

                predicted_quantity = round(
                    predicted_orders *
                    average_units_per_order
                )


                predicted_quantity = max(
                    predicted_quantity,
                    predicted_orders
                )


            else:

                predicted_quantity = 0


            # =============================================
            # FORECAST ROW
            # =============================================

            forecast.append({

                "date":
                    str(
                        forecast_date
                    ),

                "predicted_revenue":
                    round(
                        predicted_revenue,
                        2
                    ),

                "predicted_orders":
                    int(
                        predicted_orders
                    ),

                "predicted_quantity":
                    int(
                        predicted_quantity
                    ),
            })


        prediction_method = (
            "Machine Learning - "
            "Linear Regression"
        )


    # =====================================================
    # HISTORICAL AVERAGE FALLBACK
    # =====================================================

    else:


        for day_number in range(
            FORECAST_DAYS
        ):

            forecast_date = (
                forecast_start_date +
                timedelta(
                    days=day_number
                )
            )


            predicted_revenue = (
                average_daily_revenue
            )


            # =============================================
            # FALLBACK ORDERS
            # =============================================

            if (
                predicted_revenue > 0
                and
                average_order_value > 0
            ):

                predicted_orders = round(
                    predicted_revenue /
                    average_order_value
                )


                predicted_orders = max(
                    predicted_orders,
                    1
                )


            else:

                predicted_orders = 0


            # =============================================
            # FALLBACK QUANTITY
            # =============================================

            if (
                predicted_orders > 0
                and
                average_units_per_order > 0
            ):

                predicted_quantity = round(
                    predicted_orders *
                    average_units_per_order
                )


                predicted_quantity = max(
                    predicted_quantity,
                    predicted_orders
                )


            else:

                predicted_quantity = 0


            forecast.append({

                "date":
                    str(
                        forecast_date
                    ),

                "predicted_revenue":
                    round(
                        predicted_revenue,
                        2
                    ),

                "predicted_orders":
                    int(
                        predicted_orders
                    ),

                "predicted_quantity":
                    int(
                        predicted_quantity
                    ),
            })


        prediction_method = (
            "Historical Average Fallback"
        )


    # =====================================================
    # 7 DAY FORECAST TOTAL
    # =====================================================

    forecast_7_days = sum(

        safe_float(
            item[
                "predicted_revenue"
            ]
        )

        for item
        in forecast
    )


    # =====================================================
    # PREDICTED DAILY AVERAGE
    # =====================================================

    predicted_average_daily_revenue = (

        forecast_7_days /
        FORECAST_DAYS

        if FORECAST_DAYS

        else 0
    )


    # =====================================================
    # PREDICTED TOTAL ORDERS
    # =====================================================

    predicted_total_orders = sum(

        safe_int(
            item[
                "predicted_orders"
            ]
        )

        for item
        in forecast
    )


    # =====================================================
    # PREDICTED TOTAL QUANTITY
    # =====================================================

    predicted_total_quantity = sum(

        safe_int(
            item[
                "predicted_quantity"
            ]
        )

        for item
        in forecast
    )


    # =====================================================
    # BUSINESS INSIGHT
    # =====================================================

    if ml_ready:


        if (
            trend_direction ==
            "Increasing"
        ):

            trend_message = (
                "The historical revenue "
                "trend is increasing."
            )


        elif (
            trend_direction ==
            "Decreasing"
        ):

            trend_message = (
                "The historical revenue "
                "trend is decreasing."
            )


        else:

            trend_message = (
                "The historical revenue "
                "trend is relatively stable."
            )


        quality_message = (
            f"Model quality is "
            f"{model_quality}"
        )


        if (
            revenue_r2_score
            is not None
        ):

            quality_message += (
                f" with an R² score of "
                f"{revenue_r2_score:.3f}."
            )


        else:

            quality_message += "."
        

        insight = (
            "Machine Learning forecast generated "
            "using Linear Regression. "
            f"{trend_message} "
            f"{quality_message} "
            f"The forecast period starts on "
            f"{forecast_start_date.strftime('%d %b %Y')}. "
            f"The business is expected to generate "
            f"approximately "
            f"₹{forecast_7_days:,.2f} "
            f"during the next "
            f"{FORECAST_DAYS} days."
        )


    else:


        remaining_days = max(
            MINIMUM_ML_DAYS -
            actual_sales_days,
            0
        )


        insight = (
            f"Only {actual_sales_days} different "
            f"sales days are currently available. "
            f"At least {MINIMUM_ML_DAYS} sales days "
            f"are required before the Machine Learning "
            f"model is activated. "
            f"Add {remaining_days} more day(s) "
            f"of sales history. "
            f"Until then, the forecast uses the "
            f"historical daily average. "
            f"The forecast starts on "
            f"{forecast_start_date.strftime('%d %b %Y')} "
            f"and estimated revenue for the next "
            f"{FORECAST_DAYS} days is "
            f"₹{forecast_7_days:,.2f}."
        )


    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "historical":
            historical,

        "forecast":
            forecast,

        "summary": {

            "historical_revenue":
                round(
                    total_revenue,
                    2
                ),

            "historical_days":
                actual_sales_days,

            "calendar_training_days":
                calendar_training_days,

            "average_daily_revenue":
                round(
                    average_daily_revenue,
                    2
                ),

            "forecast_7_days":
                round(
                    forecast_7_days,
                    2
                ),

            "predicted_average_daily_revenue":
                round(
                    predicted_average_daily_revenue,
                    2
                ),

            "average_daily_orders":
                round(
                    average_daily_orders,
                    2
                ),

            "average_daily_quantity":
                round(
                    average_daily_quantity,
                    2
                ),

            "average_order_value":
                round(
                    average_order_value,
                    2
                ),

            "average_units_per_order":
                round(
                    average_units_per_order,
                    2
                ),

            "predicted_total_orders":
                predicted_total_orders,

            "predicted_total_quantity":
                predicted_total_quantity,
        },

        "model_info": {

            "method":
                prediction_method,

            "ml_ready":
                ml_ready,

            "training_days":
                actual_sales_days,

            "minimum_ml_days":
                MINIMUM_ML_DAYS,

            "revenue_r2_score":
                (
                    round(
                        revenue_r2_score,
                        4
                    )

                    if revenue_r2_score
                    is not None

                    else None
                ),

            "model_quality":
                model_quality,

            "revenue_trend_per_day":
                round(
                    revenue_trend_per_day,
                    2
                ),

            "trend_direction":
                trend_direction,

            "forecast_start_date":
                str(
                    forecast_start_date
                ),

            "forecast_end_date":
                str(
                    forecast_start_date +
                    timedelta(
                        days=
                            FORECAST_DAYS -
                            1
                    )
                ),

            "forecast_days":
                FORECAST_DAYS,
        },

        "insight":
            insight,

        "user_id":
            current_user.get(
                "sub"
            ),
    }