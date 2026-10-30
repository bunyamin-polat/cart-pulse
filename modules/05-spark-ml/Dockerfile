FROM apache/spark:4.2.0-python3

# Spark ML needs NumPy, which the official image leaves out.
USER root
RUN pip install --no-cache-dir numpy==2.2.6
USER spark
