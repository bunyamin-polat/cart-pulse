# Built on a supported JRE and Python instead of the official Spark image,
# which ships Python 3.10 and leaves out the NumPy that Spark ML needs.
FROM eclipse-temurin:21-jre-noble

RUN apt-get update \
    && apt-get install --yes --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir pyspark==4.3.0 numpy==2.2.6

ADD --chmod=644 https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.14/postgresql-42.7.14.jar /opt/postgresql.jar

RUN useradd --create-home spark
USER spark

ENV PATH=/opt/venv/bin:$PATH
ENV PYSPARK_PYTHON=/opt/venv/bin/python
