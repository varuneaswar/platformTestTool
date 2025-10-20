import unittest
from unittest.mock import MagicMock, patch
from src.core.query_executor import QueryExecutor

class TestRetryBehavior(unittest.TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.executor = QueryExecutor(self.mock_connection)
        
        # Mock config with retry settings
        self.retry_config = {
            'enabled': True,
            'retries': 3,
            'skip_nonrelational': True
        }
        
        self.single_run_config = 'per_thread'  # or 'per_query_once'
        
    def test_retry_on_failure(self):
        """Test that queries are retried the correct number of times on failure"""
        # Configure mock to fail initial attempts but succeed on final retry
        self.mock_connection.execute.side_effect = [
            Exception("DB Error"),  # First attempt fails
            Exception("DB Error"),  # Second attempt fails
            {"duration": 1.0}      # Third attempt succeeds
        ]
        
        queries = [{"query": "SELECT 1", "type": "relational"}]
        self.executor.retry_config = self.retry_config
        
        results = self.executor.execute_batch(queries)
        
        # Verify execute was called 3 times
        self.assertEqual(self.mock_connection.execute.call_count, 3)
        # Verify final result was returned
        self.assertEqual(results[0]["duration"], 1.0)

    def test_skip_nonrelational_retry(self):
        """Test that non-relational queries are skipped when configured"""
        # Configure mock to fail
        self.mock_connection.execute.side_effect = Exception("DB Error")
        
        queries = [{"query": "db.collection.find()", "type": "nonrelational"}]
        self.executor.retry_config = self.retry_config
        
        results = self.executor.execute_batch(queries)
        
        # Verify execute was called only once - no retries
        self.assertEqual(self.mock_connection.execute.call_count, 1)
        # Verify error was captured
        self.assertTrue("error" in results[0])

    def test_per_thread_mode(self):
        """Test that queries execute per thread when single_run_mode is 'per_thread'"""
        self.mock_connection.execute.return_value = {"duration": 1.0}
        
        # Same query from different threads
        queries = [
            {"query": "SELECT 1", "thread": "thread1"},
            {"query": "SELECT 1", "thread": "thread2"}
        ]
        self.executor.single_run_mode = 'per_thread'
        
        results = self.executor.execute_batch(queries)
        
        # Verify both queries executed
        self.assertEqual(self.mock_connection.execute.call_count, 2)
        self.assertEqual(len(results), 2)

    def test_per_query_once_mode(self):
        """Test that identical queries only execute once in 'per_query_once' mode"""
        self.mock_connection.execute.return_value = {"duration": 1.0}
        
        # Same query multiple times
        queries = [
            {"query": "SELECT 1", "thread": "thread1"},
            {"query": "SELECT 1", "thread": "thread2"},
            {"query": "SELECT 2", "thread": "thread1"}  # Different query
        ]
        self.executor.single_run_mode = 'per_query_once'
        
        results = self.executor.execute_batch(queries)
        
        # Verify unique queries executed only once
        self.assertEqual(self.mock_connection.execute.call_count, 2)
        # Verify results were duplicated appropriately
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["duration"], results[1]["duration"])
        
    def test_retry_with_duration_zero(self):
        """Test retry behavior when duration is 0 or missing"""
        # Configure mock to return zero duration then valid duration
        self.mock_connection.execute.side_effect = [
            {"duration": 0},        # First attempt returns 0
            {"duration": 1.5}       # Second attempt returns valid duration
        ]
        
        queries = [{"query": "SELECT 1", "type": "relational"}]
        self.executor.retry_config = self.retry_config
        
        results = self.executor.execute_batch(queries)
        
        # Verify execute was called twice
        self.assertEqual(self.mock_connection.execute.call_count, 2)
        # Verify final non-zero duration was used
        self.assertEqual(results[0]["duration"], 1.5)

    def test_retry_exhaustion(self):
        """Test behavior when all retries are exhausted"""
        # Configure mock to always fail
        self.mock_connection.execute.side_effect = Exception("DB Error")
        
        queries = [{"query": "SELECT 1", "type": "relational"}]
        self.executor.retry_config = self.retry_config
        
        results = self.executor.execute_batch(queries)
        
        # Verify retried maximum number of times
        self.assertEqual(self.mock_connection.execute.call_count, 
                        self.retry_config["retries"])
        # Verify error captured in results
        self.assertTrue("error" in results[0])

if __name__ == '__main__':
    unittest.main()