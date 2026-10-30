-- CREATE DATABASE has no IF NOT EXISTS, so \gexec runs it only when the query returns a row.
SELECT 'CREATE DATABASE staging'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'staging')\gexec
