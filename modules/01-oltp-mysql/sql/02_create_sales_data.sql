-- IF NOT EXISTS rather than DROP TABLE: re-running this must never wipe loaded data.
-- No surrogate key: the course fixes these five columns, and the CSV maps onto them directly.
CREATE TABLE IF NOT EXISTS sales.sales_data (
    product_id  INT UNSIGNED NOT NULL,
    customer_id INT UNSIGNED NOT NULL,
    price       DECIMAL(10, 2) NOT NULL,
    quantity    SMALLINT UNSIGNED NOT NULL,
    `timestamp` DATETIME NOT NULL
) ENGINE = InnoDB;
