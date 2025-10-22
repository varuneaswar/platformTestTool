-- Complex SELECT query for Oracle with joins and aggregations
SELECT 
    ut.table_name,
    ut.num_rows,
    uc.column_name,
    uc.data_type,
    COUNT(uc.column_name) OVER (PARTITION BY ut.table_name) as col_count
FROM user_tables ut
INNER JOIN user_tab_columns uc ON ut.table_name = uc.table_name
WHERE ut.num_rows > 0
ORDER BY ut.num_rows DESC, ut.table_name, uc.column_id
FETCH FIRST 50 ROWS ONLY
