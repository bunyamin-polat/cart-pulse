-- Labels are derived from the date itself, so they cannot disagree with the calendar.
INSERT INTO dw.dim_date (
    date_key, full_date, year, quarter, quarter_name, month, month_name, day,
    weekday, weekday_name
)
SELECT
    to_char(day, 'YYYYMMDD')::integer,
    day::date,
    extract(year FROM day)::integer,
    extract(quarter FROM day)::integer,
    'Q' || extract(quarter FROM day)::integer,
    extract(month FROM day)::integer,
    to_char(day, 'FMMonth'),
    extract(day FROM day)::integer,
    extract(isodow FROM day)::integer,
    to_char(day, 'FMDay')
FROM (
    SELECT date_trunc('year', MIN(order_date)) AS first_day,
        date_trunc('year', MAX(order_date)) + interval '1 year - 1 day' AS last_day
    FROM staging.orders
) AS bounds
CROSS JOIN LATERAL generate_series(first_day, last_day, interval '1 day') AS day
ON CONFLICT (date_key) DO NOTHING;

INSERT INTO dw.dim_country (country)
SELECT DISTINCT country FROM staging.orders
ON CONFLICT (country) DO NOTHING;

INSERT INTO dw.dim_category (category)
SELECT DISTINCT category FROM staging.orders
ON CONFLICT (category) DO NOTHING;
