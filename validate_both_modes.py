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

print("=" * 80)
print("VALIDATION OF BOTH TEST SCENARIOS")
print("=" * 80)

# Get all runs from the last hour
cur.execute("""
    SELECT 
        job_id,
        COUNT(*) as total_queries,
        MIN(start_time) as first_query,
        MAX(end_time) as last_query,
        MAX(end_time) - MIN(start_time) as duration
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
    GROUP BY job_id
    ORDER BY MIN(start_time)
""")

runs = cur.fetchall()
print(f"\nTotal Test Runs Found: {len(runs)}\n")

for idx, run in enumerate(runs, 1):
    job_id, total, first, last, duration = run
    print("=" * 80)
    print(f"RUN #{idx}: {job_id}")
    print("=" * 80)
    print(f"Total Queries: {total}")
    print(f"Duration: {duration}")
    print(f"Time Range: {first} to {last}")
    
    # Get query breakdown
    cur.execute("""
        SELECT 
            operation,
            complexity,
            COUNT(*) as count,
            ROUND(AVG(duration)::numeric, 6) as avg_duration
        FROM soak_test_metrics 
        WHERE job_id = %s
        GROUP BY operation, complexity
        ORDER BY operation, complexity
    """, (job_id,))
    
    print(f"\nQuery Breakdown:")
    print(f"{'Operation':<10} {'Complexity':<10} {'Count':>7} {'Avg Duration(s)':>18}")
    print("-" * 55)
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:<10} {row[2]:>7} {float(row[3]):>18.6f}")
    
    # Check for duplicates
    cur.execute("""
        SELECT 
            file_name,
            operation,
            complexity,
            COUNT(*) as execution_count
        FROM soak_test_metrics 
        WHERE job_id = %s
        GROUP BY file_name, operation, complexity
        ORDER BY operation, complexity, file_name
    """, (job_id,))
    
    print(f"\nFile Execution Counts:")
    print(f"{'File':<30} {'Operation':<10} {'Complexity':<10} {'Executions':>12}")
    print("-" * 65)
    
    has_duplicates = False
    unique_files = 0
    for row in cur.fetchall():
        marker = " ⚠️" if row[3] > 1 else " ✓"
        print(f"{row[0]:<30} {row[1]:<10} {row[2]:<10} {row[3]:>12}{marker}")
        unique_files += 1
        if row[3] > 1:
            has_duplicates = True
    
    # Determine test mode
    if total == unique_files:
        print(f"\n✅ TEST MODE: per_query_once (each query executed exactly once)")
    elif has_duplicates:
        print(f"\n✅ TEST MODE: per_thread (queries executed multiple times per thread)")
        # Calculate expected: 3 threads * 5 queries_per_connection = 15 total
        print(f"   Expected pattern: Each thread executes queries_per_connection times")
    
    print()

# Success rates
print("=" * 80)
print("OVERALL SUCCESS RATES")
print("=" * 80)

cur.execute("""
    SELECT 
        job_id,
        COUNT(*) as total,
        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
        ROUND((SUM(CASE WHEN success THEN 1 ELSE 0 END)::numeric / COUNT(*)::numeric * 100), 2) as success_rate
    FROM soak_test_metrics 
    WHERE start_time > NOW() - INTERVAL '1 hour'
    GROUP BY job_id
    ORDER BY MIN(start_time)
""")

print(f"\n{'Job ID':<30} {'Total':>8} {'Success':>8} {'Rate(%)':>10}")
print("-" * 60)
for row in cur.fetchall():
    print(f"{row[0]:<30} {row[1]:>8} {row[2]:>8} {float(row[3]):>10.2f}")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
