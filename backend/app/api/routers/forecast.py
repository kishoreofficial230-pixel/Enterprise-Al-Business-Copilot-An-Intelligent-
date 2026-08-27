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

RECENT_WINDOW = 7

ML_WEIGHT = 0.60

BASELINE_WEIGHT = 0.40

MIN_BASELINE_RATIO = 0.35

MAX_BASELINE_RATIO = 2.50


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def to_date(value):

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    if isinstance(
        value,
        date,
    ):
        return value

    return datetime.strptime(
        str(value),
        "%Y-%m-%d",
    ).date()


def safe_float(value):

    try:

        return float(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0


def safe_int(value):

    try:

        return int(
            value or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0


def get_model_quality(
    r2_score,
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


def get_confidence_label(
    actual_sales_days,
    r2_score,
):

    if (
        actual_sales_days <
        MINIMUM_ML_DAYS
    ):

        return "Low"

    if r2_score is None:

        return "Low"

    if (
        actual_sales_days >= 14
        and
        r2_score >= 0.70
    ):

        return "High"

    if (
        actual_sales_days >= 7
        and
        r2_score >= 0.40
    ):

        return "Moderate"

    return "Low"


def weighted_recent_average(
    values,
    window=RECENT_WINDOW,
):

    cleaned_values = []

    for value in values:

        number = safe_float(
            value
        )

        if number >= 0:

            cleaned_values.append(
                number
            )

    if not cleaned_values:

        return 0.0

    recent_values = (
        cleaned_values[
            -window:
        ]
    )

    weights = list(
        range(
            1,
            len(
                recent_values
            ) + 1,
        )
    )

    total_weight = sum(
        weights
    )

    if total_weight <= 0:

        return (
            sum(
                recent_values
            )
            /
            len(
                recent_values
            )
        )

    weighted_total = 0.0

    for (
        value,
        weight,
    ) in zip(
        recent_values,
        weights,
    ):

        weighted_total += (
            value *
            weight
        )

    return (
        weighted_total /
        total_weight
    )


def calculate_mae(
    actual_values,
    predicted_values,
):

    if (
        not actual_values
        or
        not predicted_values
    ):

        return None

    length = min(
        len(
            actual_values
        ),
        len(
            predicted_values
        ),
    )

    if length <= 0:

        return None

    total_error = 0.0

    for index in range(
        length
    ):

        total_error += abs(
            safe_float(
                actual_values[
                    index
                ]
            )
            -
            safe_float(
                predicted_values[
                    index
                ]
            )
        )

    return (
        total_error /
        length
    )


def no_data_response(
    message,
    current_user,
):

    return {

        "message":
            message,

        "historical":
            [],

        "forecast":
            [],

        "summary": {

            "historical_revenue":
                0,

            "historical_days":
                0,

            "calendar_training_days":
                0,

            "average_daily_revenue":
                0,

            "average_sales_day_revenue":
                0,

            "recent_weighted_daily_revenue":
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

            "predicted_total_orders":
                0,

            "predicted_total_quantity":
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

            "revenue_mae":
                None,

            "model_quality":
                "Not Available",

            "confidence":
                "Low",

            "revenue_trend_per_day":
                0,

            "trend_direction":
                "No Data",

            "forecast_start_date":
                None,

            "forecast_end_date":
                None,

            "forecast_days":
                FORECAST_DAYS,

            "hybrid_forecast":
                False,

            "ml_weight":
                0,

            "baseline_weight":
                1,
        },

        "insight":
            message,

        "user_id":
            current_user.get(
                "sub"
            ),
    }


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


    # =================================================
    # FETCH ACTUAL DAILY SALES
    # =================================================

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


    # =================================================
    # NO SALES DATA
    # =================================================

    if not daily_sales_query:

        return no_data_response(

            "No sales data available. "
            "Add dated sales records "
            "to generate a forecast.",

            current_user,
        )


    # =================================================
    # NORMALIZE DATABASE DATA
    # =================================================

    actual_daily_data = []


    for row in daily_sales_query:

        sale_day = to_date(
            row.sale_day
        )


        if sale_day is None:

            continue


        actual_daily_data.append({

            "date":
                sale_day,

            "revenue":
                max(
                    safe_float(
                        row.revenue
                    ),
                    0.0,
                ),

            "orders":
                max(
                    safe_int(
                        row.orders
                    ),
                    0,
                ),

            "quantity":
                max(
                    safe_int(
                        row.quantity
                    ),
                    0,
                ),
        })


    # =================================================
    # INVALID DATED SALES DATA
    # =================================================

    if not actual_daily_data:

        return no_data_response(

            "No valid dated sales "
            "records were found.",

            current_user,
        )


    # =================================================
    # FIRST / LAST SALES DATE
    # =================================================

    first_day = (
        actual_daily_data[
            0
        ][
            "date"
        ]
    )


    last_day = (
        actual_daily_data[
            -1
        ][
            "date"
        ]
    )


    calendar_training_days = (

        (
            last_day -
            first_day
        ).days
        +
        1
    )


    actual_sales_days = len(
        actual_daily_data
    )


    # =================================================
    # IMPORTANT ML FIX
    # =================================================
    #
    # Old implementation inserted zero revenue for every
    # date where no sale existed.
    #
    # Example:
    #
    # May 1  = 100000
    # May 2  = 0
    # May 3  = 0
    # May 4  = 50000
    #
    # Large numbers of artificial zero days caused the
    # regression line to fall below zero.
    #
    # Now:
    #
    # Only real sales days are used for ML training.
    #
    # =================================================


    # =================================================
    # HISTORICAL RESPONSE
    # =================================================

    historical = []


    for item in actual_daily_data:

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
                    2,
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


    # =================================================
    # HISTORICAL ARRAYS
    # =================================================

    revenues = [

        item[
            "revenue"
        ]

        for item
        in actual_daily_data
    ]


    orders = [

        item[
            "orders"
        ]

        for item
        in actual_daily_data
    ]


    quantities = [

        item[
            "quantity"
        ]

        for item
        in actual_daily_data
    ]


    # =================================================
    # TOTALS
    # =================================================

    total_revenue = sum(
        revenues
    )


    total_orders = sum(
        orders
    )


    total_quantity = sum(
        quantities
    )


    # =================================================
    # CALENDAR DAILY AVERAGES
    # =================================================

    average_daily_revenue = (

        total_revenue /
        calendar_training_days

        if calendar_training_days > 0

        else 0
    )


    average_daily_orders = (

        total_orders /
        calendar_training_days

        if calendar_training_days > 0

        else 0
    )


    average_daily_quantity = (

        total_quantity /
        calendar_training_days

        if calendar_training_days > 0

        else 0
    )


    # =================================================
    # ACTUAL SALES DAY AVERAGE
    # =================================================

    average_sales_day_revenue = (

        total_revenue /
        actual_sales_days

        if actual_sales_days > 0

        else 0
    )


    # =================================================
    # ORDER VALUE
    # =================================================

    average_order_value = (

        total_revenue /
        total_orders

        if total_orders > 0

        else 0
    )


    # =================================================
    # UNITS PER ORDER
    # =================================================

    average_units_per_order = (

        total_quantity /
        total_orders

        if total_orders > 0

        else 0
    )


    # =================================================
    # RECENT WEIGHTED BASELINE
    # =================================================

    recent_weighted_daily_revenue = (

        weighted_recent_average(
            revenues
        )
    )


    baseline_revenue = (

        recent_weighted_daily_revenue

        if (
            recent_weighted_daily_revenue >
            0
        )

        else
            average_sales_day_revenue
    )


    if (
        baseline_revenue <= 0
        and
        total_revenue > 0
    ):

        baseline_revenue = (

            total_revenue /

            max(
                actual_sales_days,
                1,
            )
        )


    # =================================================
    # ML READINESS
    # =================================================

    ml_ready = (

        actual_sales_days >=
        MINIMUM_ML_DAYS
    )


    # =================================================
    # FORECAST DATE
    # =================================================

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

        day_after_last_sale,
    )


    forecast_end_date = (

        forecast_start_date +

        timedelta(
            days=
                FORECAST_DAYS -
                1
        )
    )


    # =================================================
    # DEFAULT MODEL VALUES
    # =================================================

    forecast = []


    revenue_r2_score = None


    revenue_mae = None


    revenue_trend_per_day = 0.0


    trend_direction = (
        "Stable"
    )


    model_quality = (
        "Not Available"
    )


    confidence = (
        "Low"
    )


    prediction_method = (
        "Historical Weighted "
        "Average Fallback"
    )


    hybrid_forecast = False


    # =================================================
    # MACHINE LEARNING MODE
    # =================================================

    if ml_ready:


        # =============================================
        # SALES-DAY SEQUENCE FEATURE
        # =============================================
        #
        # We intentionally use the sequence of actual
        # sales days:
        #
        # 0, 1, 2, 3, 4 ...
        #
        # instead of generating hundreds of zero dates.
        #
        # =============================================

        X = [

            [
                index
            ]

            for index
            in range(
                actual_sales_days
            )
        ]


        # =============================================
        # TRAIN LINEAR REGRESSION MODEL
        # =============================================

        revenue_model = (
            LinearRegression()
        )


        revenue_model.fit(

            X,

            revenues,
        )


        # =============================================
        # TRAINING PREDICTIONS
        # =============================================

        training_predictions = [

            safe_float(
                value
            )

            for value
            in revenue_model.predict(
                X
            )
        ]


        # =============================================
        # R² SCORE
        # =============================================

        raw_r2_score = float(

            revenue_model.score(

                X,

                revenues,
            )
        )


        if math.isfinite(
            raw_r2_score
        ):

            revenue_r2_score = (
                raw_r2_score
            )


        # =============================================
        # MAE
        # =============================================

        revenue_mae = (

            calculate_mae(

                revenues,

                training_predictions,
            )
        )


        # =============================================
        # MODEL QUALITY
        # =============================================

        model_quality = (

            get_model_quality(
                revenue_r2_score
            )
        )


        # =============================================
        # CONFIDENCE
        # =============================================

        confidence = (

            get_confidence_label(

                actual_sales_days,

                revenue_r2_score,
            )
        )


        # =============================================
        # TREND
        # =============================================

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


        # =============================================
        # HYBRID MODEL
        # =============================================

        prediction_method = (

            "Hybrid ML - "
            "Linear Regression + "
            "Recent Weighted Baseline"
        )


        hybrid_forecast = True


        # =============================================
        # REALISTIC PREDICTION LIMITS
        # =============================================

        positive_floor = max(

            baseline_revenue *
            MIN_BASELINE_RATIO,

            0.0,
        )


        positive_cap = max(

            baseline_revenue *
            MAX_BASELINE_RATIO,

            average_sales_day_revenue *
            MAX_BASELINE_RATIO,

            positive_floor,
        )


        # =============================================
        # NEXT 7 DAYS
        # =============================================

        for day_number in range(
            FORECAST_DAYS
        ):


            forecast_date = (

                forecast_start_date +

                timedelta(
                    days=
                        day_number
                )
            )


            future_sequence_index = (

                actual_sales_days +

                day_number
            )


            # =========================================
            # RAW LINEAR REGRESSION PREDICTION
            # =========================================

            raw_ml_prediction = float(

                revenue_model.predict(

                    [
                        [
                            future_sequence_index
                        ]
                    ]
                )[0]
            )


            # =========================================
            # PREVENT NEGATIVE ML COMPONENT
            # =========================================

            ml_component = max(

                raw_ml_prediction,

                0.0,
            )


            # =========================================
            # HYBRID REVENUE PREDICTION
            # =========================================
            #
            # 60% Machine Learning
            # 40% Recent weighted sales baseline
            #
            # This prevents a weak negative regression
            # line from turning the complete forecast
            # into ₹0.
            #
            # =========================================

            predicted_revenue = (

                ML_WEIGHT *
                ml_component

                +

                BASELINE_WEIGHT *
                baseline_revenue
            )


            # =========================================
            # POSITIVE REVENUE FLOOR
            # =========================================

            if total_revenue > 0:

                predicted_revenue = max(

                    predicted_revenue,

                    positive_floor,
                )


            # =========================================
            # EXTREME VALUE CAP
            # =========================================

            if positive_cap > 0:

                predicted_revenue = min(

                    predicted_revenue,

                    positive_cap,
                )


            predicted_revenue = max(

                predicted_revenue,

                0.0,
            )


            # =========================================
            # PREDICT ORDERS
            # =========================================

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

                    1,
                )


            else:

                predicted_orders = 0


            # =========================================
            # PREDICT QUANTITY
            # =========================================

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

                    predicted_orders,
                )


            else:

                predicted_quantity = 0


            # =========================================
            # FORECAST ROW
            # =========================================

            forecast.append({

                "date":
                    str(
                        forecast_date
                    ),

                "predicted_revenue":
                    round(
                        predicted_revenue,
                        2,
                    ),

                "predicted_orders":
                    int(
                        predicted_orders
                    ),

                "predicted_quantity":
                    int(
                        predicted_quantity
                    ),

                "raw_ml_revenue":
                    round(
                        raw_ml_prediction,
                        2,
                    ),
            })


    # =================================================
    # FALLBACK FORECAST
    # =================================================

    else:


        for day_number in range(
            FORECAST_DAYS
        ):


            forecast_date = (

                forecast_start_date +

                timedelta(
                    days=
                        day_number
                )
            )


            predicted_revenue = max(

                baseline_revenue,

                0.0,
            )


            if (
                predicted_revenue > 0
                and
                average_order_value > 0
            ):

                predicted_orders = max(

                    round(
                        predicted_revenue /
                        average_order_value
                    ),

                    1,
                )


            else:

                predicted_orders = 0


            if (
                predicted_orders > 0
                and
                average_units_per_order > 0
            ):

                predicted_quantity = max(

                    round(
                        predicted_orders *
                        average_units_per_order
                    ),

                    predicted_orders,
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
                        2,
                    ),

                "predicted_orders":
                    int(
                        predicted_orders
                    ),

                "predicted_quantity":
                    int(
                        predicted_quantity
                    ),

                "raw_ml_revenue":
                    None,
            })


    # =================================================
    # 7-DAY FORECAST REVENUE
    # =================================================

    forecast_7_days = sum(

        safe_float(

            item[
                "predicted_revenue"
            ]
        )

        for item
        in forecast
    )


    # =================================================
    # PREDICTED DAILY REVENUE
    # =================================================

    predicted_average_daily_revenue = (

        forecast_7_days /
        FORECAST_DAYS

        if FORECAST_DAYS > 0

        else 0
    )


    # =================================================
    # PREDICTED TOTAL ORDERS
    # =================================================

    predicted_total_orders = sum(

        safe_int(

            item[
                "predicted_orders"
            ]
        )

        for item
        in forecast
    )


    # =================================================
    # PREDICTED TOTAL QUANTITY
    # =================================================

    predicted_total_quantity = sum(

        safe_int(

            item[
                "predicted_quantity"
            ]
        )

        for item
        in forecast
    )


    # =================================================
    # AI / BUSINESS INSIGHT
    # =================================================

    if ml_ready:


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
                f"{revenue_r2_score:.3f}"
            )


        if (
            revenue_mae
            is not None
        ):

            quality_message += (

                f" and MAE of "
                f"₹{revenue_mae:,.2f}"
            )


        quality_message += "."


        insight = (

            "Hybrid Machine Learning forecast "
            "generated using Linear Regression "
            "blended with a recent weighted "
            "business baseline. "

            f"The revenue trend is "
            f"{trend_direction.lower()}. "

            f"{quality_message} "

            f"Forecast confidence is "
            f"{confidence}. "

            f"The forecast period is "
            f"{forecast_start_date.strftime('%d %b %Y')} "
            f"to "
            f"{forecast_end_date.strftime('%d %b %Y')}. "

            f"Expected revenue for the next "
            f"{FORECAST_DAYS} days is "
            f"approximately "
            f"₹{forecast_7_days:,.2f}."
        )


    else:


        remaining_days = max(

            MINIMUM_ML_DAYS -
            actual_sales_days,

            0,
        )


        insight = (

            f"Only {actual_sales_days} different "
            f"sales day(s) are available. "

            f"At least {MINIMUM_ML_DAYS} sales "
            f"days are required before the "
            f"Machine Learning model is activated. "

            f"Add {remaining_days} more sales "
            f"day(s). "

            "Until then, the forecast uses a "
            "weighted recent sales baseline. "

            f"Estimated revenue for the next "
            f"{FORECAST_DAYS} days is "
            f"₹{forecast_7_days:,.2f}."
        )


    # =================================================
    # FINAL RESPONSE
    # =================================================

    return {

        "historical":
            historical,


        "forecast":
            forecast,


        "summary": {

            "historical_revenue":
                round(
                    total_revenue,
                    2,
                ),

            "historical_days":
                actual_sales_days,

            "calendar_training_days":
                calendar_training_days,

            "average_daily_revenue":
                round(
                    average_daily_revenue,
                    2,
                ),

            "average_sales_day_revenue":
                round(
                    average_sales_day_revenue,
                    2,
                ),

            "recent_weighted_daily_revenue":
                round(
                    recent_weighted_daily_revenue,
                    2,
                ),

            "forecast_7_days":
                round(
                    forecast_7_days,
                    2,
                ),

            "predicted_average_daily_revenue":
                round(
                    predicted_average_daily_revenue,
                    2,
                ),

            "average_daily_orders":
                round(
                    average_daily_orders,
                    2,
                ),

            "average_daily_quantity":
                round(
                    average_daily_quantity,
                    2,
                ),

            "average_order_value":
                round(
                    average_order_value,
                    2,
                ),

            "average_units_per_order":
                round(
                    average_units_per_order,
                    2,
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
                        4,
                    )

                    if (
                        revenue_r2_score
                        is not None
                    )

                    else None
                ),

            "revenue_mae":
                (
                    round(
                        revenue_mae,
                        2,
                    )

                    if (
                        revenue_mae
                        is not None
                    )

                    else None
                ),

            "model_quality":
                model_quality,

            "confidence":
                confidence,

            "revenue_trend_per_day":
                round(
                    revenue_trend_per_day,
                    2,
                ),

            "trend_direction":
                trend_direction,

            "forecast_start_date":
                str(
                    forecast_start_date
                ),

            "forecast_end_date":
                str(
                    forecast_end_date
                ),

            "forecast_days":
                FORECAST_DAYS,

            "hybrid_forecast":
                hybrid_forecast,

            "ml_weight":
                (
                    ML_WEIGHT

                    if ml_ready

                    else 0
                ),

            "baseline_weight":
                (
                    BASELINE_WEIGHT

                    if ml_ready

                    else 1
                ),
        },


        "insight":
            insight,


        "user_id":
            current_user.get(
                "sub"
            ),
    }