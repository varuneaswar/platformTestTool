-- Simple UPDATE query for Oracle
-- Note: This is an example. Adjust table and columns based on your schema.
UPDATE test_table 
SET name = 'Updated Entry',
    modified_date = SYSDATE
WHERE id = 1
