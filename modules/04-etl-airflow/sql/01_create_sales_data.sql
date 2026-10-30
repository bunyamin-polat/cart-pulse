-- The spelling of timeestamp is required by the course.
-- The defaults exist because the MySQL source has no price or timestamp columns.
CREATE TABLE IF NOT EXISTS public.sales_data (
    rowid       integer NOT NULL,
    product_id  integer NOT NULL,
    customer_id integer NOT NULL,
    price       decimal DEFAULT 0.0 NOT NULL,
    quantity    integer NOT NULL,
    timeestamp  timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (rowid)
);
