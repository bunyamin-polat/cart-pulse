INSERT INTO dw.fact_sales (
    order_id, date_key, country_key, category_key, amount, status
)
SELECT
    o.order_id,
    to_char(o.order_date, 'YYYYMMDD')::integer,
    c.country_key,
    k.category_key,
    o.amount,
    o.status
FROM staging.orders o
JOIN dw.dim_country c ON c.country = o.country
JOIN dw.dim_category k ON k.category = o.category
ON CONFLICT (order_id) DO UPDATE SET
    date_key = EXCLUDED.date_key,
    country_key = EXCLUDED.country_key,
    category_key = EXCLUDED.category_key,
    amount = EXCLUDED.amount,
    status = EXCLUDED.status
WHERE (dw.fact_sales.date_key, dw.fact_sales.country_key, dw.fact_sales.category_key,
        dw.fact_sales.amount, dw.fact_sales.status)
    IS DISTINCT FROM
    (EXCLUDED.date_key, EXCLUDED.country_key, EXCLUDED.category_key,
        EXCLUDED.amount, EXCLUDED.status);
