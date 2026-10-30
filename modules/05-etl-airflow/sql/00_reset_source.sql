-- sales.sql creates the table without IF NOT EXISTS, so a re-run has to drop it first.
CREATE DATABASE IF NOT EXISTS sales;
USE sales;
DROP TABLE IF EXISTS sales_data;
