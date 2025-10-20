from typing import Dict, Any, List
import time
import json
import statistics
from dataclasses import dataclass, asdict
import pandas as pd
from datetime import datetime

@dataclass
class QueryMetrics:
    # Identifiers (required)
    query_id: str
    
    # Timing (required)
    start_time: float
    end_time: float
    duration: float
    
    # Identifiers (optional)
    thread_name: str = ''
    
    # Query Info
    query_gist: str = ''
    operation: str = ''
    complexity: str = ''
    file_name: str = ''
    
    # Performance Metrics
    rows_affected: int = 0
    memory_usage: float = None
    cpu_time: float = None
    
    # Status/Error Info
    success: bool = False
    error: str = ''
    error_code: str = ''
    return_code: str = ''

@dataclass
class ConnectionMetrics:
    connection_id: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_duration: float
    min_duration: float
    max_duration: float
    total_rows_affected: int
    timestamp: datetime

class PerformanceMetrics:
    """Collects and analyzes performance metrics for database operations."""
    
    def __init__(self):
        # Structured dataclass metrics (used for aggregations)
        self.query_metrics: List[QueryMetrics] = []
        # Raw/normalized metric dicts (used for export/reporting)
        self.raw_query_metrics: List[Dict[str, Any]] = []
        self.connection_metrics: Dict[str, List[ConnectionMetrics]] = {}

    def record_query_metrics(self, query_id: str, metrics: Dict[str, Any]):
        """
        Record metrics for a single query execution.
        
        Args:
            query_id: Unique identifier for the query
            metrics: Dictionary containing query execution metrics
        """
        import datetime
        def iso8601(ts):
            try:
                return datetime.datetime.utcfromtimestamp(float(ts)).isoformat() if ts else None
            except Exception:
                return None

        # Normalize raw metric dict so exports contain consistent fields
        norm = dict(metrics) if isinstance(metrics, dict) else {}
        norm.setdefault('query_id', query_id)

        # derive identifiers from query_id ONLY if not already provided in metrics
        try:
            parts = str(norm.get('query_id', '')).split('_')
            if not norm.get('job_id'):
                norm['job_id'] = parts[0] if len(parts) > 0 else ''
            if not norm.get('test_case_id'):
                norm['test_case_id'] = parts[1] if len(parts) > 1 else ''
            # user_id can contain underscores; prefer provided value
            if 'user_id' not in norm or not norm.get('user_id'):
                norm['user_id'] = parts[2] if len(parts) > 2 else ''
            # Prefer provided thread_name; avoid parsing from query_id when present
            if 'thread_name' not in norm or not norm.get('thread_name'):
                norm['thread_name'] = metrics.get('thread_name', '')
        except Exception:
            norm.setdefault('job_id', '')
            norm.setdefault('test_case_id', '')
            norm.setdefault('user_id', '')
            norm.setdefault('thread_name', '')

        def safe_int(val, default=None):
            try:
                return int(val) if val is not None else default
            except (ValueError, TypeError):
                return default
                
        def safe_float(val, default=None):
            try:
                return float(val) if val is not None else default
            except (ValueError, TypeError):
                return default

        def normalize_path(path):
            if not path:
                return ''
            # Convert absolute path to relative path from query_folder
            query_folder = 'queries/'
            try:
                path = path.replace('\\', '/')
                if query_folder in path:
                    return path[path.index(query_folder):]
                return path
            except Exception:
                return path

        # Timing metrics - always required
        norm['duration'] = safe_float(metrics.get('total_duration', metrics.get('duration')), 0.0)
        norm['start_time'] = safe_float(metrics.get('start_time'))
        norm['end_time'] = safe_float(metrics.get('end_time'))
        norm['total_duration'] = norm['duration']  # Backward compatibility

        # Query information
        norm['query'] = metrics.get('query', '')
        norm['query_gist'] = (norm['query'] or '')[:200].strip()
        norm['file_name'] = normalize_path(metrics.get('file_name', ''))
        norm['operation'] = metrics.get('operation', '').lower()
        norm['complexity'] = metrics.get('complexity', '').lower()

        # Status and error fields - nulls as empty strings
        norm['success'] = bool(metrics.get('success', False))
        norm['error'] = metrics.get('error', '') or ''
        # Preserve numeric return_code values like 0/1/9 (avoid falsy 0 becoming empty)
        norm['return_code'] = metrics.get('return_code', None)
        norm['error_code'] = metrics.get('error_code', '') or ''
        
        # Performance metrics - nulls as None
        norm['rows_affected'] = safe_int(metrics.get('rows_affected', metrics.get('rows_processed')), 0)
        norm['rows_processed'] = norm['rows_affected']  # Match rows_affected
        norm['memory_usage'] = safe_float(metrics.get('memory_usage'), None)
        norm['cpu_time'] = safe_float(metrics.get('cpu_time'), None)

        # Add ISO8601 datetime fields for human readability (after norm is defined)
        norm['start_time_iso'] = iso8601(norm.get('start_time'))
        norm['end_time_iso'] = iso8601(norm.get('end_time'))

        # store raw normalized metric for export/reporting
        self.raw_query_metrics.append(norm)

        # keep dataclass-based metrics for backward-compatible aggregation
        try:
            query_metric = QueryMetrics(
                query_id=query_id,
                start_time=norm.get('start_time') or 0,
                end_time=norm.get('end_time') or 0,
                duration=norm.get('duration', 0.0),
                success=norm.get('success', False),
                error=norm.get('error'),
                rows_affected=norm.get('rows_affected', 0),
                memory_usage=norm.get('memory_usage', 0),
                cpu_time=norm.get('cpu_time', 0)
            )
            self.query_metrics.append(query_metric)
        except Exception:
            # If dataclass conversion fails, still keep raw metric
            pass

    def calculate_connection_metrics(self, connection_id: str) -> ConnectionMetrics:
        """
        Calculate aggregated metrics for a database connection.
        
        Args:
            connection_id: Identifier for the database connection
            
        Returns:
            ConnectionMetrics object containing aggregated metrics
        """
        metrics = [m for m in self.query_metrics if m.query_id.startswith(connection_id)]
        
        if not metrics:
            return None
            
        durations = [m.duration for m in metrics]
        successful = [m for m in metrics if m.success]
        
        connection_metric = ConnectionMetrics(
            connection_id=connection_id,
            total_queries=len(metrics),
            successful_queries=len(successful),
            failed_queries=len(metrics) - len(successful),
            avg_duration=statistics.mean(durations) if durations else 0,
            min_duration=min(durations) if durations else 0,
            max_duration=max(durations) if durations else 0,
            total_rows_affected=sum(m.rows_affected for m in metrics),
            timestamp=datetime.now()
        )
        
        if connection_id not in self.connection_metrics:
            self.connection_metrics[connection_id] = []
        self.connection_metrics[connection_id].append(connection_metric)
        
        return connection_metric

    def get_performance_report(self, connection_id: str = None) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Args:
            connection_id: Optional connection ID to filter metrics
            
        Returns:
            Dictionary containing the performance report
        """
        # Use raw normalized metrics for reporting (richer fields)
        if connection_id:
            metrics = [m for m in self.raw_query_metrics if m.get('query_id', '').startswith(connection_id)]
            conn_metrics = self.connection_metrics.get(connection_id, [])
        else:
            metrics = self.raw_query_metrics
            conn_metrics = [m for metrics_list in self.connection_metrics.values() for m in metrics_list]
            
        if not metrics:
            return {"error": "No metrics found for the specified criteria"}
            
        # Convert metrics to pandas DataFrames for analysis
        # Build DataFrame from raw metric dicts for accurate columns
        df_queries = pd.DataFrame(metrics)
        df_connections = pd.DataFrame([asdict(m) for m in conn_metrics]) if conn_metrics else pd.DataFrame()

        # Helper to convert pandas/numpy scalars to native Python types
        def to_native(x):
            try:
                if pd.isna(x):
                    return None
            except Exception:
                pass
            try:
                return int(x)
            except Exception:
                pass
            try:
                return float(x)
            except Exception:
                pass
            return x

        total_queries = len(metrics)
        success_count = int(df_queries['success'].sum()) if 'success' in df_queries.columns else 0
        avg_duration = df_queries['duration'].mean() if 'duration' in df_queries.columns else None
        # support rows_affected or rows_processed
        rows_col = 'rows_affected' if 'rows_affected' in df_queries.columns else ('rows_processed' if 'rows_processed' in df_queries.columns else None)
        total_rows = int(df_queries[rows_col].sum()) if rows_col else 0

        percentiles = {}
        if 'duration' in df_queries.columns and total_queries > 0:
            percentiles = {
                'p50': to_native(df_queries['duration'].quantile(0.5)),
                'p90': to_native(df_queries['duration'].quantile(0.9)),
                'p95': to_native(df_queries['duration'].quantile(0.95)),
                'p99': to_native(df_queries['duration'].quantile(0.99)),
            }

        report = {
            "summary": {
                "total_queries": total_queries,
                "success_rate": to_native((success_count / total_queries * 100) if total_queries > 0 else 0),
                "avg_duration": to_native(avg_duration) if avg_duration is not None else None,
                "total_rows_affected": to_native(total_rows)
            },
            "performance_trends": {
                "duration_percentiles": percentiles
            },
            "error_analysis": {
                "error_count": int((~df_queries['success']).sum()) if 'success' in df_queries.columns else 0,
                "error_rate": to_native((len(df_queries[~df_queries['success']]) / total_queries * 100) if total_queries > 0 else 0),
                "common_errors": df_queries[~df_queries['success']]['error'].value_counts().to_dict() if 'error' in df_queries.columns else {}
            }
        }

        return report

    def export_metrics(self, file_path: str):
        """
        Export all metrics to a JSON file.
        
        Args:
            file_path: Path to save the metrics file
        """
        # Export raw normalized metrics for complete reporting
        export_data = {
            "query_metrics": self.raw_query_metrics,
            "connection_metrics": {
                conn_id: [asdict(m) for m in metrics]
                for conn_id, metrics in self.connection_metrics.items()
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, default=str, indent=2)

    def clear_metrics(self, connection_id: str = None):
        """
        Clear stored metrics.
        
        Args:
            connection_id: Optional connection ID to clear specific metrics
        """
        if connection_id:
            self.query_metrics = [m for m in self.query_metrics if not m.query_id.startswith(connection_id)]
            self.connection_metrics.pop(connection_id, None)
        else:
            self.query_metrics.clear()
            self.connection_metrics.clear()