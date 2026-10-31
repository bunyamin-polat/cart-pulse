\echo 'Total sales by year, with a grand total'
SELECT COALESCE(year::text, 'All years') AS year, SUM(total_sales) AS total_sales
FROM marts.sales_by_year_country
GROUP BY ROLLUP (year)
ORDER BY year;

\echo 'Top 5 countries'
SELECT country, SUM(total_sales) AS total_sales
FROM marts.sales_by_year_country
GROUP BY country
ORDER BY total_sales DESC
LIMIT 5;

\echo 'Sales by category'
SELECT category, SUM(total_sales) AS total_sales
FROM marts.sales_by_category_country
GROUP BY category
ORDER BY total_sales DESC;

\echo 'Latest load'
SELECT source, rows_extracted, rows_changed, loaded_at
FROM etl.load_audit
ORDER BY load_id DESC
LIMIT 3;
