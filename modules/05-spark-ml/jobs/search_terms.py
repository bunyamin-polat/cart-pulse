"""Analyze the search terms logged by the e-commerce web server."""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc

DATA_FILE = "/opt/cartpulse/data/searchterms.csv"


def main():
    spark = SparkSession.builder.appName("SearchTerms").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    df = spark.read.csv(DATA_FILE, header=True, inferSchema=True)

    print("Rows and columns:", df.count(), len(df.columns))

    print("Top 5 rows:")
    df.show(5, truncate=False)

    print("Data type of searchterm:", dict(df.dtypes)["searchterm"])

    gaming_laptop = df.filter(col("searchterm") == "gaming laptop").count()
    print("Searches for gaming laptop:", gaming_laptop)

    # The term breaks ties so the output is the same on every run.
    print("Top 5 search terms:")
    df.groupBy("searchterm").count().orderBy(desc("count"), "searchterm").show(
        5, truncate=False
    )

    spark.stop()


if __name__ == "__main__":
    main()
