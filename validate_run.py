import psycopg2
from datetime import datetime, timedelta

# Connect to database
conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    database='postgres',
    user='postgres',
    password='admin'
)
cur = conn.cursor()

# Get the most recent run data (last hour)
print("=" * 80)
print("RECENT RUN VALIDATION (Last Hour)")
print("=" * 80)

cur.execute("""
    SELECT 
        COUNT(*) as total_records,
        MIN(start_time) as first_record,
        MAX(end_time) as last_record,
        MAX(end_time) - MIN(start_time) as duration
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
""")
result = cur.fetchone()
print(f"\nTotal Records: {result[0]}")
print(f"First Record: {result[1]}")
print(f"Last Record: {result[2]}")
print(f"Test Duration: {result[3]}")

# Check job_id distribution
print("\n" + "=" * 80)
print("JOB_ID ANALYSIS")
print("=" * 80)
cur.execute("""
    SELECT 
        CASE 
            WHEN job_id = '' OR job_id IS NULL THEN '<EMPTY>'
            ELSE job_id 
        END as job_id_display,
        COUNT(*) as count,
        MIN(start_time) as first_time,
        MAX(end_time) as last_time
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
    GROUP BY job_id
    ORDER BY MIN(start_time) DESC
""")
for row in cur.fetchall():
    print(f"\nJob ID: {row[0]}")
    print(f"  Records: {row[1]}")
    print(f"  Time Range: {row[2]} to {row[3]}")

# Operation breakdown
print("\n" + "=" * 80)
print("OPERATION BREAKDOWN (Recent Run)")
print("=" * 80)
cur.execute("""
    SELECT 
        operation,
        complexity,
        COUNT(*) as count,
        ROUND(AVG(duration)::numeric, 6) as avg_duration_sec,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed,
        SUM(rows_affected) as total_rows_affected
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
    GROUP BY operation, complexity
    ORDER BY operation, complexity
""")
print(f"\n{'Operation':<10} {'Complexity':<10} {'Count':>7} {'Avg Dur(s)':>12} {'Success':>8} {'Failed':>7} {'Rows':>8}")
print("-" * 80)
for row in cur.fetchall():
    print(f"{row[0]:<10} {row[1]:<10} {row[2]:>7} {float(row[3]):>12.6f} {row[4]:>8} {row[5]:>7} {row[6]:>8}")

# Check unique query files
print("\n" + "=" * 80)
print("UNIQUE QUERY FILES (for per_query_once validation)")
print("=" * 80)
cur.execute("""
    SELECT 
        file_name,
        operation,
        complexity,
        COUNT(*) as execution_count
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
    GROUP BY file_name, operation, complexity
    ORDER BY operation, complexity, file_name
""")
print(f"\n{'File Name':<30} {'Operation':<10} {'Complexity':<10} {'Executions':>12}")
print("-" * 80)
duplicate_count = 0
for row in cur.fetchall():
    marker = " ⚠️ DUPLICATE!" if row[3] > 1 else ""
    if row[3] > 1:
        duplicate_count += 1
    print(f"{row[0]:<30} {row[1]:<10} {row[2]:<10} {row[3]:>12}{marker}")

if duplicate_count > 0:
    print(f"\n⚠️  WARNING: Found {duplicate_count} query files executed more than once!")
    print("   Expected: Each query file should execute exactly once in 'per_query_once' mode")
else:
    print(f"\n✅ PASS: All query files executed exactly once (as expected for 'per_query_once' mode)")

# Thread distribution
print("\n" + "=" * 80)
print("THREAD DISTRIBUTION")
print("=" * 80)
cur.execute("""
    SELECT 
        thread_name,
        COUNT(*) as query_count,
        MIN(start_time) as first_query,
        MAX(end_time) as last_query
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
    GROUP BY thread_name
    ORDER BY thread_name
""")
print(f"\n{'Thread Name':<30} {'Queries':>8} {'First Query':<30} {'Last Query':<30}")
print("-" * 80)
for row in cur.fetchall():
    print(f"{row[0]:<30} {row[1]:>8} {str(row[2]):<30} {str(row[3]):<30}")

# Success rate
print("\n" + "=" * 80)
print("SUCCESS RATE")
print("=" * 80)
cur.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed,
        ROUND((SUM(CASE WHEN success THEN 1 ELSE 0 END)::numeric / COUNT(*)::numeric * 100), 2) as success_rate
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
""")
result = cur.fetchone()
print(f"\nTotal Queries: {result[0]}")
print(f"Successful: {result[1]} ({result[3]}%)")
print(f"Failed: {result[2]}")

# Expected vs Actual validation
print("\n" + "=" * 80)
print("CONFIGURATION VALIDATION")
print("=" * 80)
print("\nExpected from quick_read_smoke.json:")
print("  - execution_time: 0 (single run mode)")
print("  - single_run_mode: per_query_once")
print("  - concurrent_connections: 6 threads")
print("  - Thread ratios: 90% read (40% simple, 30% medium, 30% complex), 10% write")
print("  - Write: 100% insert, simple complexity")
print("\nValidation:")
cur.execute("""
    SELECT 
        CASE WHEN operation = 'select' THEN 'READ' ELSE 'WRITE' END as query_type,
        COUNT(*) as count,
        ROUND((COUNT(*)::numeric / (SELECT COUNT(*) FROM soak_test_metrics WHERE start_time > NOW() - INTERVAL '1 hour')::numeric * 100), 1) as percentage
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
    GROUP BY CASE WHEN operation = 'select' THEN 'READ' ELSE 'WRITE' END
""")
for row in cur.fetchall():
    expected = "~90%" if row[0] == 'READ' else "~10%"
    print(f"  {row[0]}: {row[1]} queries ({row[2]}%) - Expected: {expected}")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
