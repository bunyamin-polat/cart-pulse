"""Daily pipeline that extracts client IPs from the web server log and archives them."""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

DATA_DIR = "/opt/airflow/data"

default_args = {
    "owner": "cartpulse",
    "start_date": datetime(2026, 10, 1),
    "email": ["data-team@example.com"],
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# catchup=False runs only the latest interval, not one run per day since start_date.
with DAG(
    dag_id="process_web_log",
    default_args=default_args,
    description="Extract, filter and archive client IPs from the web server log",
    schedule="@daily",
    catchup=False,
) as dag:
    extract_data = BashOperator(
        task_id="extract_data",
        bash_command=(
            f"cut -d' ' -f1 {DATA_DIR}/accesslog.txt > {DATA_DIR}/extracted_data.txt"
        ),
    )

    # -x matches whole lines and -F treats the dots literally, so similar IPs survive.
    transform_data = BashOperator(
        task_id="transform_data",
        bash_command=(
            "grep -vxF '198.46.149.143' "
            f"{DATA_DIR}/extracted_data.txt > {DATA_DIR}/transformed_data.txt"
        ),
    )

    # -C stores the file without the container path inside the archive.
    load_data = BashOperator(
        task_id="load_data",
        bash_command=(
            f"tar -cf {DATA_DIR}/weblog.tar -C {DATA_DIR} transformed_data.txt"
        ),
    )

    extract_data >> transform_data >> load_data
