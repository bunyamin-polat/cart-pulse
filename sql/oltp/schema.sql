-- Runs on the first start of the MySQL volume.
CREATE TABLE IF NOT EXISTS orders (
    order_id   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_date DATE NOT NULL,
    country    VARCHAR(100) NOT NULL,
    category   VARCHAR(50) NOT NULL,
    amount     DECIMAL(12, 2) NOT NULL,
    status     ENUM('completed', 'cancelled') NOT NULL DEFAULT 'completed',
    -- MySQL maintains this column, so the ETL also sees corrections to old orders.
    updated_at TIMESTAMP(6) NOT NULL
        DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (order_id),
    INDEX idx_orders_updated_at (updated_at),
    INDEX idx_orders_order_date (order_date)
) ENGINE = InnoDB;
