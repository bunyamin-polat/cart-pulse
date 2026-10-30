-- TRUNCATE keeps the load idempotent: a second run must not double the row count.
TRUNCATE TABLE sales.sales_data;

-- The file has no header row, so nothing is skipped.
LOAD DATA INFILE '/var/lib/mysql-files/oltpdata.csv'
INTO TABLE sales.sales_data
FIELDS TERMINATED BY ','
LINES TERMINATED BY '\n'
(product_id, customer_id, price, quantity, `timestamp`);

SELECT COUNT(*) FROM sales.sales_data;
