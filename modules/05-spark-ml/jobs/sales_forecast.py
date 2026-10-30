"""Train a monthly sales model on warehouse data and forecast 2023."""

from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression, LinearRegressionModel
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, lit
from pyspark.sql.functions import sum as sum_

DATA_FILE = "/opt/cartpulse/data/monthly_sales.csv"
MODEL_PATH = "/opt/cartpulse/data/sales_forecast.model"


def build_features(frame):
    """Turn year and month into one continuous time feature."""
    assembler = VectorAssembler(inputCols=["time"], outputCol="features")
    with_time = frame.withColumn("time", col("year") + col("month") / 12)
    return assembler.transform(with_time)


def train(frame):
    regression = LinearRegression(
        featuresCol="features", labelCol="sales", maxIter=100, regParam=0.1
    )
    return regression.fit(frame)


def backtest(data):
    """Compare the model with a plain average on a year it has not seen."""
    history = data.filter(col("year") < 2021)
    holdout = data.filter(col("year") == 2021)

    evaluator = RegressionEvaluator(labelCol="sales", metricName="rmse")
    model_rmse = evaluator.evaluate(train(history).transform(holdout))

    average = history.agg(avg("sales")).first()[0]
    baseline_rmse = evaluator.evaluate(
        holdout.withColumn("prediction", lit(float(average)))
    )

    print(f"Backtest on 2021, model RMSE: {model_rmse:,.0f}")
    print(f"Backtest on 2021, average RMSE: {baseline_rmse:,.0f}")


def main():
    spark = SparkSession.builder.appName("SalesForecast").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    sales = spark.read.csv(DATA_FILE, header=True, inferSchema=True)
    data = build_features(sales)

    backtest(data)

    trained = train(data)
    print(f"R2 on all data: {trained.summary.r2:.3f}")

    # Reloading proves the saved files are enough, without the training step.
    trained.write().overwrite().save(MODEL_PATH)
    print("Saved model:", MODEL_PATH)
    model = LinearRegressionModel.load(MODEL_PATH)

    months = spark.createDataFrame(
        [(2023, month) for month in range(1, 13)], ["year", "month"]
    )
    forecast = model.transform(build_features(months))
    total = forecast.agg(sum_("prediction")).first()[0]
    print(f"Forecast sales for 2023: {total:,.0f}")

    spark.stop()


if __name__ == "__main__":
    main()
