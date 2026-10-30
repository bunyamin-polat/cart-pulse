-- Year and month come from the date itself, because DimDate's month labels disagree with
-- the calendar on some days.
COPY (
    SELECT
        EXTRACT(YEAR FROM d.date)::int AS year,
        EXTRACT(MONTH FROM d.date)::int AS month,
        SUM(f.amount) AS sales
    FROM "FactSales" f
    JOIN "DimDate" d ON f.dateid = d.dateid
    GROUP BY 1, 2
    ORDER BY 1, 2
) TO STDOUT WITH (FORMAT csv, HEADER true);
