"""Publish how often each term is searched on the storefront."""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, desc
from warehouse import replace_table

DATA_FILE = "/opt/cartpulse/data/raw/searchterms.csv"


def main():
    spark = SparkSession.builder.appName("SearchTerms").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    searches = spark.read.csv(DATA_FILE, header=True, inferSchema=True)
    ranking = (
        searches.groupBy(col("searchterm").alias("search_term"))
        .count()
        .withColumnRenamed("count", "searches")
        .orderBy(desc("searches"), "search_term")
    )

    replace_table(ranking, "marts.top_search_terms")
    ranking.show(5, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()
