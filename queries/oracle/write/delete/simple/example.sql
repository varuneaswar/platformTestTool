-- Simple DELETE query for Oracle
-- Note: This is an example. Adjust table and conditions based on your schema.
DELETE FROM test_table 
WHERE created_date < SYSDATE - 30
