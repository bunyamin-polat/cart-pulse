CREATE SCHEMA IF NOT EXISTS etl;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS marts;

CREATE TABLE IF NOT EXISTS etl.watermarks (
    source          text PRIMARY KEY,
    high_water_mark timestamp NOT NULL,
    updated_at      timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS etl.load_audit (
    load_id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source         text NOT NULL,
    rows_extracted bigint NOT NULL,
    rows_changed   bigint NOT NULL,
    rows_excluded  bigint NOT NULL DEFAULT 0,
    rows_rejected  bigint NOT NULL DEFAULT 0,
    loaded_at      timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.orders (
    order_id   bigint PRIMARY KEY,
    order_date date NOT NULL,
    country    text NOT NULL,
    category   text NOT NULL,
    amount     numeric(12, 2) NOT NULL,
    status     text NOT NULL,
    updated_at timestamp NOT NULL,
    loaded_at  timestamp NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staging.catalog_products (
    product_id   text PRIMARY KEY,
    product_type text NOT NULL,
    model        text NOT NULL,
    screen_size  numeric(5, 2),
    ram          text,
    hard_disk    text
);

CREATE TABLE IF NOT EXISTS staging.web_requests (
    client_ip    inet NOT NULL,
    requested_at timestamptz NOT NULL,
    method       text NOT NULL,
    path         text NOT NULL,
    status       integer NOT NULL,
    bytes        bigint
);

CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key     integer PRIMARY KEY,
    full_date    date NOT NULL UNIQUE,
    year         integer NOT NULL,
    quarter      integer NOT NULL,
    quarter_name text NOT NULL,
    month        integer NOT NULL,
    month_name   text NOT NULL,
    day          integer NOT NULL,
    weekday      integer NOT NULL,
    weekday_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_country (
    country_key integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country     text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.dim_category (
    category_key integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category     text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS dw.fact_sales (
    order_id     bigint PRIMARY KEY,
    date_key     integer NOT NULL REFERENCES dw.dim_date (date_key),
    country_key  integer NOT NULL REFERENCES dw.dim_country (country_key),
    category_key integer NOT NULL REFERENCES dw.dim_category (category_key),
    amount       numeric(12, 2) NOT NULL,
    status       text NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON dw.fact_sales (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_country ON dw.fact_sales (country_key);

-- Written by the Spark jobs.
CREATE TABLE IF NOT EXISTS marts.sales_forecast (
    forecast_month  date PRIMARY KEY,
    predicted_sales numeric(14, 2) NOT NULL,
    model           text NOT NULL,
    backtest_rmse   numeric(14, 2) NOT NULL,
    baseline_rmse   numeric(14, 2) NOT NULL,
    generated_at    timestamp NOT NULL
);

CREATE TABLE IF NOT EXISTS marts.top_search_terms (
    search_term text PRIMARY KEY,
    searches    bigint NOT NULL
);
