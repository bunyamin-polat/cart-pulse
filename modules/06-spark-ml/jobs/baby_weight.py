"""Train, save and reload a small model that predicts infant weight from height."""

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression, LinearRegressionModel
from pyspark.sql import SparkSession

MODEL_PATH = "/opt/cartpulse/data/babyweightprediction.model"

HEIGHT_AND_WEIGHT = [
    (46, 2.5),
    (51, 3.4),
    (54, 4.4),
    (57, 5.1),
    (60, 5.6),
    (61, 6.1),
    (63, 6.4),
]


def build_assembler():
    """Build the feature step. It needs a running session, so it cannot be global."""
    return VectorAssembler(inputCols=["height"], outputCol="features")


def predict(spark, model, height):
    """Print the predicted weight in kilograms for a height in centimeters."""
    heights = spark.createDataFrame([(height,)], ["height"])
    features = build_assembler().transform(heights)
    prediction = model.transform(features).first()["prediction"]
    print(f"Predicted weight at {height} cm: {prediction:.2f} kg")


def main():
    spark = SparkSession.builder.appName("BabyWeight").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    data = spark.createDataFrame(HEIGHT_AND_WEIGHT, ["height", "weight"])
    data.show()

    training = build_assembler().transform(data).select("features", "weight")
    regression = LinearRegression(
        featuresCol="features", labelCol="weight", maxIter=100, regParam=0.1
    )
    trained = regression.fit(training)

    # Reloading proves the saved files are enough, without the training step.
    trained.write().overwrite().save(MODEL_PATH)
    print("Saved model:", MODEL_PATH)
    model = LinearRegressionModel.load(MODEL_PATH)

    predict(spark, model, 70)
    predict(spark, model, 50)

    spark.stop()


if __name__ == "__main__":
    main()
