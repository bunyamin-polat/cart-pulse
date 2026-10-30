-- TRUNCATE restores the initial warehouse state, which leaves new rows for the ETL to find.
TRUNCATE TABLE public.sales_data;

-- The explicit column list maps the CSV's timestamp column onto timeestamp.
COPY public.sales_data (rowid, product_id, customer_id, price, quantity, timeestamp)
FROM '/import-etl/sales.csv'
WITH (FORMAT csv, HEADER true);
