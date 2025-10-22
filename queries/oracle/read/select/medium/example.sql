-- Medium complexity SELECT query for Oracle
SELECT 
    table_name, 
    tablespace_name, 
    num_rows,
    blocks,
    avg_row_len
FROM user_tables 
WHERE num_rows > 0
ORDER BY num_rows DESC
FETCH FIRST 10 ROWS ONLY
