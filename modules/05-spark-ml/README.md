# Module 5: Big Data Analytics with Spark

## Goal

Analyze e-commerce search terms with Apache Spark, and train, save and reload Spark ML models to forecast 2023 sales.

## Run it

From the repository root:

```bash
make setup             # then replace the placeholder passwords in .env
make up
make load-warehouse    # the forecast trains on warehouse data
make spark-build
make spark-search      # analyze the search terms
make spark-persistence # save and reload a small example model
make spark-forecast    # train the sales model and forecast 2023
```

Spark runs through `docker compose run`. Each job starts a container, finishes and exits, so nothing keeps using memory between jobs.

## Search term analysis

[search_terms.py](jobs/search_terms.py) reads `searchterms.csv` into a DataFrame.

| Question | Result |
| --- | --- |
| Rows and columns | 10,000 rows, 4 columns |
| Data type of `searchterm` | `string` |
| Searches for `gaming laptop` | 499 |
| Top term | `mobile 6 inch`, with 2,312 searches |

The next four terms are `mobile 5g` (2,301), `mobile latest` (1,327), `laptop` (935) and `tablet wifi` (896).

## Saving and loading a model

[model_persistence.py](jobs/model_persistence.py) trains a linear regression on seven height and weight pairs, saves it, reloads it from disk and predicts. It gives 7.86 kg at 70 cm and 3.47 kg at 50 cm. Separating training from serving is the core MLOps idea here: a saved model can make predictions without being trained again.

## Sales forecast

[sales_forecast.py](jobs/sales_forecast.py) trains on 36 months of warehouse sales, exported by [export_monthly_sales.sql](sql/export_monthly_sales.sql). It takes year and month from the real date, because the `DimDate` month labels disagree with the calendar on some days.

| Measure | Result |
| --- | --- |
| Backtest on 2021, model RMSE | 1,027,984 |
| Backtest on 2021, plain average RMSE | 1,024,477 |
| R² on all data | 0.013 |
| Forecast sales for 2023 | 404,657,224 |

### Reading the result

**The model is no better than a plain average.** Yearly sales barely move, at 399.7M, 400.4M and 400.8M, so there is no trend to learn. The forecast effectively says that sales stay flat. The dataset is synthetic, so this is the expected result, and the backtest is what makes that visible.

### The course's pretrained model

The course provides `sales_prediction.model`, saved with Spark 2.4.3. It still loads on Spark 4.2.0 and predicts 175.17 for 2023. This project trains its own model because that one was trained on unknown data and its scale cannot be compared with the warehouse. It is used only to answer the course quiz, and no job in this repository depends on it.

## Design decisions

- **Spark 4.2.0.** The older 3.5.1 image ships Python 3.8, which is past end of life.
- **A small Dockerfile.** The official image leaves out NumPy, and Spark ML cannot start without it.
- **A baseline in the backtest.** A model only matters when it beats the simplest alternative.
- **A code fix from the course notebook.** Sessions come from `SparkSession` alone, without `findspark` or a separate `SparkContext`.

### Known trade-offs

- **Local mode.** Jobs run on one machine, so they show the API and not cluster behavior.
- **Python 3.10 comes from the image.** It reaches end of life in October 2026.
- **`netlib` messages are harmless.** The image has no native math libraries, so Spark falls back to its Java implementation.
- **Linear regression on a date** cannot capture seasonality. It suits this flat data, and real sales data would need a seasonal model.

## Key learnings

- **Lazy evaluation changes how you read Spark code.** Transformations build a plan, and actions such as `count` run it.
- **Always test against a baseline.** A forecast of 404.7M looks precise, but the backtest shows that it adds nothing to an average.
- **A low score can be the honest answer.** Reporting that the data has no trend is more useful than a flattering metric.
- **Check what a base image contains.** Both the missing NumPy and the old Python came from the image, not from project code.
- **Model files outlive versions.** A model saved with Spark 2.4.3 still loaded on 4.2.0.
