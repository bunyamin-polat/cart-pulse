-- The senior engineer's improved schema lives in its own database, as the course requires.
SELECT 'CREATE DATABASE "Test1"'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'Test1')\gexec
