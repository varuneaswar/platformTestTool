-- Simple INSERT query for Oracle
-- Note: This is an example. Adjust table and columns based on your schema.
INSERT INTO test_table (id, name, created_date) 
VALUES (test_seq.NEXTVAL, 'Test Entry', SYSDATE)
