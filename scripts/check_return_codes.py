import psycopg2
from psycopg2.extras import RealDictCursor


def main():
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        database='postgres',
        user='postgres',
        password='admin'
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT job_id
                FROM soak_test_metrics
                ORDER BY start_time DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            if not row:
                print("No rows found in soak_test_metrics")
                return
            job_id = row['job_id']
            print(f"Latest job_id: {job_id}")

            cur.execute(
                """
                SELECT return_code, COUNT(*) AS count
                FROM soak_test_metrics
                WHERE job_id = %s
                GROUP BY return_code
                ORDER BY return_code NULLS FIRST
                """,
                (job_id,)
            )
            results = cur.fetchall()
            for r in results:
                print(f"return_code={r['return_code']} count={r['count']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
