-- Rebuilt from the source files on every run, so a re-run cannot duplicate rows.
-- The view depends on the tables and has to go first.
DROP MATERIALIZED VIEW IF EXISTS total_sales_per_country;
DROP TABLE IF EXISTS public."FactSales", public."DimDate", public."DimCategory", public."DimCountry";

\i /import/CREATE-SCRIPT.sql

-- HEADER skips the first line, which also discards the BOM at the start of DimCountry.csv.
COPY public."DimDate" FROM '/import/DimDate.csv' WITH (FORMAT csv, HEADER true);
COPY public."DimCategory" FROM '/import/DimCategory.csv' WITH (FORMAT csv, HEADER true);
COPY public."DimCountry" FROM '/import/DimCountry.csv' WITH (FORMAT csv, HEADER true);
COPY public."FactSales" FROM '/import/FactSales.csv' WITH (FORMAT csv, HEADER true);
