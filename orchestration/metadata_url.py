"""Print the Airflow metadata database URL.

Airflow reads this through its _CMD setting, so servers and CLI commands all share it.
"""

import os
from urllib.parse import quote

password = quote(os.environ["POSTGRES_PASSWORD"], safe="")
print(f"postgresql+psycopg2://postgres:{password}@postgres:5432/airflow", end="")
