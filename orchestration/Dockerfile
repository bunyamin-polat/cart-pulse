FROM apache/airflow:3.3.2-python3.12

# PostgreSQL support comes with the image, and the sources need their own drivers.
RUN pip install --no-cache-dir mysql-connector-python==26.10.0 pymongo==4.19.0 python-dotenv==1.2.4

COPY start.sh metadata_url.py /opt/cartpulse/

CMD ["bash", "/opt/cartpulse/start.sh"]
