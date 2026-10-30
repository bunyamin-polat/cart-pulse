-- MySQL has no CREATE INDEX IF NOT EXISTS, so the check keeps this safe to re-run.
SET @create_ts = IF(
    EXISTS (
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = 'sales'
          AND table_name = 'sales_data'
          AND index_name = 'ts'
    ),
    'DO 0',
    'CREATE INDEX ts ON sales.sales_data (`timestamp`)'
);
PREPARE create_ts FROM @create_ts;
EXECUTE create_ts;
DEALLOCATE PREPARE create_ts;
