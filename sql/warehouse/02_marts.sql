-- Cancelled orders stay in the fact table for audit and are left out of revenue.
CREATE MATERIALIZED VIEW IF NOT EXISTS marts.sales_by_year_country AS
SELECT d.year, c.country, SUM(f.amount) AS total_sales, COUNT(*) AS orders
FROM dw.fact_sales f
JOIN dw.dim_date d USING (date_key)
JOIN dw.dim_country c USING (country_key)
WHERE f.status = 'completed'
GROUP BY d.year, c.country
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS marts.sales_by_month_category AS
SELECT d.year, d.month, d.month_name, k.category, SUM(f.amount) AS total_sales,
    COUNT(*) AS orders
FROM dw.fact_sales f
JOIN dw.dim_date d USING (date_key)
JOIN dw.dim_category k USING (category_key)
WHERE f.status = 'completed'
GROUP BY d.year, d.month, d.month_name, k.category
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS marts.sales_by_quarter_country AS
SELECT d.year, d.quarter_name, c.country, SUM(f.amount) AS total_sales,
    COUNT(*) AS orders
FROM dw.fact_sales f
JOIN dw.dim_date d USING (date_key)
JOIN dw.dim_country c USING (country_key)
WHERE f.status = 'completed'
GROUP BY d.year, d.quarter_name, c.country
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS marts.sales_by_category_country AS
SELECT k.category, c.country, SUM(f.amount) AS total_sales, COUNT(*) AS orders
FROM dw.fact_sales f
JOIN dw.dim_category k USING (category_key)
JOIN dw.dim_country c USING (country_key)
WHERE f.status = 'completed'
GROUP BY k.category, c.country
WITH NO DATA;

-- The forecast must not treat a month that is still in progress as a low month.
CREATE MATERIALIZED VIEW IF NOT EXISTS marts.monthly_sales AS
SELECT
    date_trunc('month', d.full_date)::date AS month,
    SUM(f.amount) AS total_sales,
    COUNT(*) AS orders,
    (date_trunc('month', d.full_date) + interval '1 month - 1 day')::date
        <= (SELECT MAX(order_date) FROM staging.orders) AS is_complete
FROM dw.fact_sales f
JOIN dw.dim_date d USING (date_key)
WHERE f.status = 'completed'
GROUP BY date_trunc('month', d.full_date)
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS marts.catalog_summary AS
SELECT product_type, COUNT(*) AS products, AVG(screen_size) AS avg_screen_size
FROM staging.catalog_products
GROUP BY product_type
WITH NO DATA;

CREATE MATERIALIZED VIEW IF NOT EXISTS marts.web_traffic_daily AS
SELECT
    requested_at::date AS day,
    COUNT(*) AS requests,
    COUNT(DISTINCT client_ip) AS visitors,
    COUNT(*) FILTER (WHERE status >= 500) AS server_errors,
    SUM(bytes) AS bytes_served
FROM staging.web_requests
GROUP BY requested_at::date
WITH NO DATA;
