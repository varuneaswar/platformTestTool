from typing import Dict, List
import os
import glob
import queue

def _read_sql_file(path: str) -> str:
    """Read SQL file content."""
    with open(path, "r", encoding="utf-8") as fh:
        content = fh.read().strip()
        # Skip comment-only files
        if content and not content.startswith('--'):
            return content
    return ""

class QueueManager:
    """
    Loads queries from folder structure:
    queries/<db_type>/read/select/{simple,medium,complex}/
    queries/<db_type>/write/{insert,update,delete}/{simple,medium,complex}/
    and creates python queue.Queue objects per (operation, complexity).
    """
    
    def __init__(self, base_folder: str, max_queue_size: int = 1000):
        self.base = base_folder
        self.max_size = max_queue_size
        self.queues: Dict[str, queue.Queue] = {}

    def _discover_files(self, op_type: str, operation: str, complexity: str):
        """Discover query files for a specific operation and complexity."""
        folder = os.path.join(self.base, op_type, operation, complexity)
        pattern = os.path.join(folder, "*.sql")
        return glob.glob(pattern)

    def load_queries(self):
        """Load all queries into queues organized by operation and complexity."""
        # Read operations
        for complexity in ["simple", "medium", "complex"]:
            key = f"read_select_{complexity}"
            q = queue.Queue(maxsize=self.max_size)
            files = self._discover_files("read", "select", complexity)
            
            for p in files:
                sql = _read_sql_file(p)
                if sql:
                    q.put({
                        "file_path": p,
                        "file_name": os.path.basename(p),
                        "operation": "select",
                        "complexity": complexity,
                        "query": sql,
                        "query_gist": sql[:200]
                    })
            
            # Fallback query if no files found
            if q.empty():
                q.put({
                    "file_path": "",
                    "file_name": "default.sql",
                    "operation": "select",
                    "complexity": complexity,
                    "query": "SELECT current_date",
                    "query_gist": "SELECT current_date"
                })
            
            self.queues[key] = q
        
        # Write operations
        write_ops = ["insert", "update", "delete"]
        for op in write_ops:
            for complexity in ["simple", "medium", "complex"]:
                key = f"write_{op}_{complexity}"
                q = queue.Queue(maxsize=self.max_size)
                files = self._discover_files("write", op, complexity)
                
                for p in files:
                    sql = _read_sql_file(p)
                    if sql:
                        q.put({
                            "file_path": p,
                            "file_name": os.path.basename(p),
                            "operation": op,
                            "complexity": complexity,
                            "query": sql,
                            "query_gist": sql[:200]
                        })
                
                # Fallback query if no files found
                if q.empty():
                    q.put({
                        "file_path": "",
                        "file_name": "default.sql",
                        "operation": op,
                        "complexity": complexity,
                        "query": "SELECT version()",
                        "query_gist": "SELECT version()"
                    })
                
                self.queues[key] = q

    def get_queue(self, op_type: str, operation: str, complexity: str) -> queue.Queue:
        """Get queue for specific operation and complexity."""
        key = f"{op_type}_{operation}_{complexity}"
        return self.queues.get(key, queue.Queue())

    def replenish_queues(self):
        """Replenish queues by reloading queries."""
        # Store current queue contents
        backup = {}
        for key, q in self.queues.items():
            items = []
            while not q.empty():
                try:
                    items.append(q.get_nowait())
                except queue.Empty:
                    break
            backup[key] = items
        
        # Refill queues
        for key, items in backup.items():
            q = self.queues[key]
            for item in items:
                if not q.full():
                    try:
                        q.put_nowait(item)
                    except queue.Full:
                        break
