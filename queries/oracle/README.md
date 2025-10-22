# Oracle Query Examples

This directory contains example SQL queries for testing Oracle databases with the Database Soak Testing Framework.

## Directory Structure

```
oracle/
├── read/
│   └── select/
│       ├── simple/      # Basic SELECT queries
│       ├── medium/      # Moderate complexity queries
│       └── complex/     # Complex queries with joins, aggregations
└── write/
    ├── insert/
    │   ├── simple/      # Basic INSERT queries
    │   ├── medium/      # INSERT with subqueries
    │   └── complex/     # Batch INSERTs
    ├── update/
    │   ├── simple/      # Basic UPDATE queries
    │   ├── medium/      # UPDATE with joins
    │   └── complex/     # Complex UPDATE queries
    └── delete/
        ├── simple/      # Basic DELETE queries
        ├── medium/      # DELETE with subqueries
        └── complex/     # Complex DELETE queries
```

## Usage Notes

1. **Customize for your schema**: The example queries use placeholder tables and columns. Replace them with actual tables from your Oracle database schema.

2. **Sequences**: Oracle uses sequences for auto-incrementing values. Example:
   ```sql
   INSERT INTO test_table (id, name) VALUES (test_seq.NEXTVAL, 'Value')
   ```

3. **Date functions**: Oracle uses `SYSDATE` for current timestamp instead of PostgreSQL's `current_timestamp`.

4. **Pagination**: Oracle 12c+ uses `FETCH FIRST n ROWS ONLY` instead of `LIMIT`.

5. **Test table setup**: Before running tests, ensure you have appropriate test tables. Example:
   ```sql
   CREATE TABLE test_table (
       id NUMBER PRIMARY KEY,
       name VARCHAR2(100),
       created_date DATE DEFAULT SYSDATE,
       modified_date DATE
   );
   
   CREATE SEQUENCE test_seq START WITH 1 INCREMENT BY 1;
   ```

## Oracle-Specific Considerations

- **Connection**: Use service name or SID for database connection
- **Permissions**: Ensure the test user has appropriate SELECT, INSERT, UPDATE, DELETE permissions
- **Tablespaces**: Consider using dedicated tablespaces for test data
- **Rollback**: Long-running write operations may require larger UNDO tablespace

## Configuration Example

See `configs/oracle_example.json` for a complete configuration example with Oracle connection settings.
