-- PostgreSQL's equivalent of an MQT. Stored results keep this report from scanning FactSales,
-- at the cost of needing REFRESH MATERIALIZED VIEW after new data arrives.
CREATE MATERIALIZED VIEW total_sales_per_country AS
SELECT c.country, SUM(f.amount) AS total_sales
FROM "FactSales" f
JOIN "DimCountry" c ON f.countryid = c.countryid
GROUP BY c.country
WITH DATA;
