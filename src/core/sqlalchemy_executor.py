from .executor import Executor
from typing import Dict, Sequence, Any
import time
import traceback

class SQLAlchemyExecutor(Executor):
    def __init__(self, connection):
        """
        connection: SQLAlchemy connection or engine object with execute() support.
        """
        self.conn = connection

    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import text
        
        result = {
            "query_id": query.get("query_id"),
            "start_time": None,
            "end_time": None,
            "duration": None,
            "success": False,
            "rows_affected": 0,
            "rows_processed": 0,
            "error": None,
            "return_code": None,
            "error_code": None,
            "memory_usage": 0,
            "cpu_time": 0,
        }
        
        # Preserve metadata
        for k in ("file_name", "operation", "complexity", "query", "query_gist"):
            if k in query:
                result[k] = query[k]
        
        try:
            result["start_time"] = time.time()
            # SQL text safe wrapper
            sql = text(query.get("query", ""))
            
            # Use connection context manager for proper execution
            with self.conn.connect() as connection:
                res = connection.execute(sql)
                
                # best-effort rowcount
                try:
                    result["rows_affected"] = getattr(res, "rowcount", 0)
                    result["rows_processed"] = result["rows_affected"]
                except Exception:
                    result["rows_affected"] = 0
                    result["rows_processed"] = 0
            
            result["end_time"] = time.time()
            result["duration"] = result["end_time"] - result["start_time"]
            result["success"] = True
            
        except Exception as e:
            result["end_time"] = time.time()
            result["duration"] = (result["end_time"] - result["start_time"]) if result["start_time"] else 0.0
            result["error"] = str(e)
            result["error_code"] = type(e).__name__
            
        return result

    def execute_batch(self, queries: Sequence[Dict[str, Any]]) -> Sequence[Dict[str, Any]]:
        out = []
        for q in queries:
            out.append(self.execute(q))
        return out
