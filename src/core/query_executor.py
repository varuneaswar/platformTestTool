from typing import Dict, Any, List, Optional
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from sqlalchemy.engine import Engine

class QueryExecutor:
    """Handles query execution and performance monitoring."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.logger = logging.getLogger(__name__)

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a single query and collect performance metrics.
        
        Args:
            query: SQL query to execute
            params: Optional query parameters
            
        Returns:
            Dictionary containing execution metrics and results
        """
        start_time = time.time()
        result = None
        error = None
        start_exec_time = None
        end_exec_time = None

        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                start_exec_time = time.time()
                result = connection.execute(text(query), params or {})
                end_exec_time = time.time()

                # Convert results to DataFrame for easier handling
                if hasattr(result, 'returns_rows') and result.returns_rows:
                    rows = result.fetchall()
                    cols = result.keys()
                    result = pd.DataFrame(rows, columns=cols)

        except Exception as e:
            error = str(e)
            self.logger.error(f"Query execution failed: {error}")

        end_time = time.time()

        exec_duration = None
        if start_exec_time is not None and end_exec_time is not None:
            exec_duration = end_exec_time - start_exec_time

        metrics = {
            'start_time': start_time,
            'end_time': end_time,
            'total_duration': end_time - start_time,
            'execution_duration': exec_duration,
            'success': error is None,
            'error': error,
            'result': result
        }

        return metrics

    def execute_batch(self, queries: List[Dict[str, Any]], max_workers: int = 5) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in parallel and collect performance metrics.
        
        Args:
            queries: List of dictionaries containing queries and parameters
                Each dictionary should have:
                - query: SQL query string
                - params: Optional parameters dictionary
            max_workers: Maximum number of concurrent executions
            
        Returns:
            List of dictionaries containing execution metrics for each query
        """
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for query_info in queries:
                future = executor.submit(
                    self.execute_query,
                    query_info['query'],
                    query_info.get('params')
                )
                futures.append(future)
            
            results = []
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Batch execution error: {str(e)}")
                    results.append({
                        'success': False,
                        'error': str(e)
                    })
                    
        return results

    def analyze_query_plan(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the execution plan for a query.
        
        Args:
            query: SQL query to analyze
            params: Optional query parameters
            
        Returns:
            Dictionary containing the query plan and analysis
        """
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                if 'postgresql' in self.engine.url.drivername:
                    explain_query = f"EXPLAIN (FORMAT JSON) {query}"
                elif 'mysql' in self.engine.url.drivername:
                    explain_query = f"EXPLAIN FORMAT=JSON {query}"
                elif 'mssql' in self.engine.url.drivername:
                    explain_query = f"SET SHOWPLAN_XML ON; {query}; SET SHOWPLAN_XML OFF;"
                else:
                    raise ValueError("Query plan analysis not supported for this database type")

                result = connection.execute(text(explain_query), params or {})
                try:
                    plan = result.fetchall()
                except Exception:
                    plan = []

                return {
                    'success': True,
                    'plan': plan,
                    'query': query
                }

        except Exception as e:
            self.logger.error(f"Query plan analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }