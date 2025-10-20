from .reporter import Reporter
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DbReporter(Reporter):
    def __init__(self, db_conn, user_id: str, table_name: str = "soak_test_metrics"):
        self.db_conn = db_conn
        self.user_id = user_id
        self.table_name = table_name
        self._buffer = []

    def record(self, metric: Dict[str, Any]) -> None:
        self._buffer.append(metric)

    def finalize(self) -> None:
        """Insert buffered metrics into database."""
        from sqlalchemy import text
        
        if not self._buffer:
            return
        
        insert_sql = text(f'''
            INSERT INTO {self.table_name} (
                job_id, test_case_id, start_time, end_time, duration, success, error, 
                rows_affected, memory_usage, cpu_time, query_gist, file_name, 
                operation, complexity, thread_name, return_code, error_code, error_desc, rows_processed
            ) VALUES (
                :job_id, :test_case_id, to_timestamp(:start_time), to_timestamp(:end_time), 
                :duration, :success, :error, :rows_affected, :memory_usage, :cpu_time,
                :query_gist, :file_name, :operation, :complexity, :thread_name, 
                :return_code, :error_code, :error_desc, :rows_processed
            )
        ''')
        
        try:
            with self.db_conn.begin() as conn:
                for m in self._buffer:
                    # Extract fields from metric
                    parts = m.get('query_id', '').split('_')
                    test_case_id = m.get('test_case_id') or (parts[1] if len(parts) > 1 else '')
                    thread_name = m.get('thread_name') or ('_'.join(parts[3:7]) if len(parts) > 6 else '')
                    
                    params = {
                        'job_id': m.get('job_id', ''),
                        'test_case_id': test_case_id,
                        'start_time': m.get('start_time', 0),
                        'end_time': m.get('end_time', 0),
                        'duration': m.get('duration', 0),
                        'success': m.get('success', False),
                        'error': m.get('error', ''),
                        'rows_affected': m.get('rows_affected', 0),
                        'memory_usage': m.get('memory_usage', 0),
                        'cpu_time': m.get('cpu_time', 0),
                        'query_gist': (m.get('query', '') or '')[:200],
                        'file_name': m.get('file_name', ''),
                        'operation': m.get('operation', ''),
                        'complexity': m.get('complexity', ''),
                        'thread_name': thread_name,
                        'return_code': m.get('return_code', ''),
                        'error_code': m.get('error_code', ''),
                        'error_desc': m.get('error', ''),
                        'rows_processed': m.get('rows_processed', 0)
                    }
                    try:
                        conn.execute(insert_sql, params)
                    except Exception as e:
                        logger.exception(f"DB insert failed: {e}")
        except Exception as e:
            logger.exception(f"DB finalize failed: {e}")
