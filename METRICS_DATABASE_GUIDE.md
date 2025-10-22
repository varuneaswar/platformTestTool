# Metrics Database Configuration - Quick Reference Guide

## Overview
This feature allows you to store test metrics in a separate database, keeping them isolated from your test target database.

## Setup Steps

### 1. Create Metrics Database
```bash
# PostgreSQL
createdb metrics_db
createuser metrics_user -P

# MySQL
mysql -u root -p
CREATE DATABASE metrics_db;
CREATE USER 'metrics_user'@'%' IDENTIFIED BY 'metrics_password';
GRANT ALL PRIVILEGES ON metrics_db.* TO 'metrics_user'@'%';
FLUSH PRIVILEGES;
```

### 2. Create Metrics Table
```bash
# PostgreSQL
psql -U metrics_user -d metrics_db -f configs/metrics_table_schema.sql

# MySQL
mysql -u metrics_user -p metrics_db < configs/metrics_table_schema.sql
```

### 3. Create Configuration File
Copy and customize one of the templates:
```bash
cp configs/metrics_db.json my_metrics_config.json
```

Edit `my_metrics_config.json`:
```json
{
    "metrics_database": {
        "db_type": "postgresql",
        "host": "your-metrics-server.com",
        "port": 5432,
        "database": "metrics_db",
        "username": "metrics_user",
        "password": "your-password",
        "table_name": "soak_test_metrics"
    }
}
```

### 4. Run Tests with Metrics Database
```bash
python main.py \
    --config configs/read_heavy_load.json \
    --metrics-config my_metrics_config.json
```

## Validation

Validate your configuration before running tests:
```bash
python validate_metrics_config.py
```

## Benefits

1. **Isolation**: Keep metrics separate from test target database
2. **Performance**: Avoid impacting test database with metrics writes
3. **Centralization**: Store metrics from multiple test targets in one place
4. **Analysis**: Query metrics across different test runs easily
5. **Security**: Use different credentials for metrics storage

## Configuration Options

### Required Fields
- `db_type`: Database type (postgresql, mysql, mssql, oracle)
- `host`: Database server hostname/IP
- `port`: Database server port
- `database`: Database name
- `username`: Database username
- `password`: Database password

### Optional Fields
- `table_name`: Name of metrics table (default: soak_test_metrics)

## Backward Compatibility

The feature is optional. If no metrics config is provided, metrics are stored in the test target database (original behavior).

```bash
# Old behavior still works
python main.py --config configs/read_heavy_load.json
```

## Example Queries

Once metrics are stored, you can query them:

```sql
-- Get metrics for a specific job
SELECT * FROM soak_test_metrics WHERE job_id = 'YOUR_JOB_ID';

-- Calculate average duration by operation
SELECT operation, AVG(duration) as avg_duration
FROM soak_test_metrics
WHERE job_id = 'YOUR_JOB_ID'
GROUP BY operation;

-- Get success rate by complexity
SELECT complexity, 
       COUNT(*) as total,
       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
       ROUND(100.0 * SUM(CASE WHEN success THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM soak_test_metrics
WHERE job_id = 'YOUR_JOB_ID'
GROUP BY complexity;
```

## Troubleshooting

### Connection Errors
If you see connection errors:
1. Verify database is running and accessible
2. Check credentials in config file
3. Verify user has necessary permissions
4. Check firewall/network settings

### Missing Table
If you see "table does not exist" errors:
1. Run the schema SQL script
2. Verify table was created: `\dt` (PostgreSQL) or `SHOW TABLES;` (MySQL)
3. Check user has SELECT/INSERT permissions

### Validation
Always validate configs before running:
```bash
python validate_metrics_config.py
```

## Support

For issues or questions:
- Check the main README.md for detailed documentation
- Review the SQL schema in configs/metrics_table_schema.sql
- Verify configurations with validate_metrics_config.py
