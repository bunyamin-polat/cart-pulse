"""Forecast the next 12 months of sales and publish the best tested model."""

from datetime import date, datetime
from decimal import Decimal
from math import sqrt
from statistics import fmean

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.linalg import Vectors
from pyspark.ml.regression import LinearRegression
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    DecimalType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from warehouse import read_table, replace_table

HORIZON = 12
MIN_IMPROVEMENT = 0.05
FORECAST_SCHEMA = StructType(
    [
        StructField("forecast_month", DateType()),
        StructField("predicted_sales", DecimalType(14, 2)),
        StructField("model", StringType()),
        StructField("backtest_rmse", DecimalType(14, 2)),
        StructField("baseline_rmse", DecimalType(14, 2)),
        StructField("generated_at", TimestampType()),
    ]
)


def money(value):
    return Decimal(f"{value:.2f}")


def rmse(actual, predicted):
    errors = [(a - p) ** 2 for a, p in zip(actual, predicted, strict=True)]
    return sqrt(fmean(errors))


def average_forecast(history, periods):
    """The baseline: every future month equals the average past month."""
    return [fmean(history)] * periods


def trend_forecast(spark, history, periods):
    """Fit a straight line through time and extend it into the future."""
    rows = [(float(i), sales) for i, sales in enumerate(history)]
    training = VectorAssembler(inputCols=["time"], outputCol="features").transform(
        spark.createDataFrame(rows, ["time", "sales"])
    )
    model = LinearRegression(labelCol="sales", regParam=0.1).fit(training)

    future = [(Vectors.dense([float(len(history) + i)]),) for i in range(periods)]
    predictions = model.transform(spark.createDataFrame(future, ["features"]))
    return [row["prediction"] for row in predictions.collect()]


def next_months(last_month, periods):
    months = []
    year, month = last_month.year, last_month.month
    for _ in range(periods):
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
        months.append(date(year, month, 1))
    return months


def main():
    spark = SparkSession.builder.appName("SalesForecast").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    rows = (
        read_table(spark, "marts.monthly_sales")
        .filter("is_complete")
        .orderBy("month")
        .collect()
    )
    months = [row["month"] for row in rows]
    sales = [float(row["total_sales"]) for row in rows]

    # Score both models on the last year, which neither of them saw during training.
    history, holdout = sales[:-HORIZON], sales[-HORIZON:]
    trend_rmse = rmse(holdout, trend_forecast(spark, history, HORIZON))
    baseline_rmse = rmse(holdout, average_forecast(history, HORIZON))
    print(f"Backtest RMSE, linear trend: {trend_rmse:,.0f}")
    print(f"Backtest RMSE, average month: {baseline_rmse:,.0f}")

    # A small gap is noise, so the simpler model wins unless the trend clearly beats it.
    if trend_rmse < baseline_rmse * (1 - MIN_IMPROVEMENT):
        model, best_rmse = "linear_trend", trend_rmse
        forecast = trend_forecast(spark, sales, HORIZON)
    else:
        model, best_rmse = "average_month", baseline_rmse
        forecast = average_forecast(sales, HORIZON)

    generated_at = datetime.now()
    published = spark.createDataFrame(
        [
            (
                month,
                money(value),
                model,
                money(best_rmse),
                money(baseline_rmse),
                generated_at,
            )
            for month, value in zip(
                next_months(months[-1], HORIZON), forecast, strict=True
            )
        ],
        FORECAST_SCHEMA,
    )
    replace_table(published, "marts.sales_forecast")

    print(f"Published model: {model}")
    print(f"Forecast for the next {HORIZON} months: {sum(forecast):,.0f}")

    spark.stop()


if __name__ == "__main__":
    main()
