-- Task 5: totals per country and per category, as two separate groupings.
SELECT c.country, k.category, SUM(f.amount) AS totalsales
FROM "FactSales" f
JOIN "DimCountry" c ON f.countryid = c.countryid
JOIN "DimCategory" k ON f.categoryid = k.categoryid
GROUP BY GROUPING SETS (c.country, k.category)
ORDER BY c.country, k.category;

-- Task 6: totals per year and country, with yearly subtotals and a grand total.
SELECT d.year, c.country, SUM(f.amount) AS totalsales
FROM "FactSales" f
JOIN "DimDate" d ON f.dateid = d.dateid
JOIN "DimCountry" c ON f.countryid = c.countryid
GROUP BY ROLLUP (d.year, c.country)
ORDER BY d.year, c.country;

-- Task 7: average sales for every combination of year and country.
SELECT d.year, c.country, AVG(f.amount) AS average_sales
FROM "FactSales" f
JOIN "DimDate" d ON f.dateid = d.dateid
JOIN "DimCountry" c ON f.countryid = c.countryid
GROUP BY CUBE (d.year, c.country)
ORDER BY d.year, c.country;

-- Task 8: read the stored results.
SELECT * FROM total_sales_per_country ORDER BY total_sales DESC LIMIT 5;
