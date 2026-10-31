"""Load the sources into the warehouse, check the data and publish the marts."""

from datetime import UTC, datetime, timedelta

from airflow.sdk import dag, task


@dag(
    dag_id="cartpulse_daily",
    description="Daily load of orders, catalog and web traffic into the warehouse",
    schedule="@daily",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["warehouse"],
)
def cartpulse_daily():
    @task
    def prepare_warehouse():
        from cartpulse import pipeline

        pipeline.prepare_warehouse()

    @task
    def load_orders():
        from cartpulse import pipeline

        pipeline.load_orders()

    @task
    def load_catalog():
        from cartpulse import pipeline

        pipeline.load_catalog()

    @task
    def load_web_traffic():
        from cartpulse import pipeline

        pipeline.load_web_traffic()

    @task
    def build_warehouse():
        from cartpulse import pipeline

        pipeline.build_warehouse()

    @task
    def check_quality():
        from cartpulse import pipeline

        pipeline.check_quality()

    @task
    def refresh_marts():
        from cartpulse import pipeline

        pipeline.refresh_marts()

    sources = [load_orders(), load_catalog(), load_web_traffic()]
    prepared = prepare_warehouse()
    built = build_warehouse()
    prepared >> sources >> built
    built >> check_quality() >> refresh_marts()


cartpulse_daily()
