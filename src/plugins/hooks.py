from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class HookManager:
    """
    Manages pre and post query execution hooks.
    Hooks allow extending functionality without modifying core code.
    """
    
    def __init__(self):
        self.pre_query_hooks: List[Callable] = []
        self.post_query_hooks: List[Callable] = []
        self.pre_test_hooks: List[Callable] = []
        self.post_test_hooks: List[Callable] = []
    
    def register_pre_query_hook(self, hook: Callable):
        """
        Register a hook to run before each query execution.
        
        Hook signature: hook(query: str, context: dict) -> dict
        - query: The SQL query to be executed
        - context: Dict with execution context (thread_id, operation, etc.)
        - Returns: Modified context (or same context)
        """
        self.pre_query_hooks.append(hook)
    
    def register_post_query_hook(self, hook: Callable):
        """
        Register a hook to run after each query execution.
        
        Hook signature: hook(result: dict, context: dict) -> dict
        - result: Query execution result (duration, success, error, etc.)
        - context: Dict with execution context
        - Returns: Modified result (or same result)
        """
        self.post_query_hooks.append(hook)
    
    def register_pre_test_hook(self, hook: Callable):
        """
        Register a hook to run before test starts.
        
        Hook signature: hook(config: dict) -> None
        - config: Test configuration dictionary
        """
        self.pre_test_hooks.append(hook)
    
    def register_post_test_hook(self, hook: Callable):
        """
        Register a hook to run after test completes.
        
        Hook signature: hook(results: dict) -> None
        - results: Test results and metrics
        """
        self.post_test_hooks.append(hook)
    
    def run_pre_query_hooks(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all pre-query hooks."""
        for hook in self.pre_query_hooks:
            try:
                context = hook(query, context) or context
            except Exception as e:
                logger.error(f"Error in pre-query hook: {e}", exc_info=True)
        return context
    
    def run_post_query_hooks(self, result: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all post-query hooks."""
        for hook in self.post_query_hooks:
            try:
                result = hook(result, context) or result
            except Exception as e:
                logger.error(f"Error in post-query hook: {e}", exc_info=True)
        return result
    
    def run_pre_test_hooks(self, config: Dict[str, Any]):
        """Execute all pre-test hooks."""
        for hook in self.pre_test_hooks:
            try:
                hook(config)
            except Exception as e:
                logger.error(f"Error in pre-test hook: {e}", exc_info=True)
    
    def run_post_test_hooks(self, results: Dict[str, Any]):
        """Execute all post-test hooks."""
        for hook in self.post_test_hooks:
            try:
                hook(results)
            except Exception as e:
                logger.error(f"Error in post-test hook: {e}", exc_info=True)
    
    def clear_all_hooks(self):
        """Clear all registered hooks."""
        self.pre_query_hooks.clear()
        self.post_query_hooks.clear()
        self.pre_test_hooks.clear()
        self.post_test_hooks.clear()


# Example hooks for reference

def example_pre_query_hook(query: str, context: dict) -> dict:
    """Example: Log query before execution."""
    logger.info(f"About to execute query on thread {context.get('thread_id')}: {query[:50]}...")
    return context

def example_post_query_hook(result: dict, context: dict) -> dict:
    """Example: Log slow queries."""
    duration = result.get('duration', 0)
    if duration > 5.0:  # Slow query threshold: 5 seconds
        logger.warning(f"Slow query detected (${duration:.2f}s): {context.get('query_gist', '')}")
    return result

def example_pre_test_hook(config: dict):
    """Example: Log test configuration."""
    logger.info(f"Starting test with {config.get('concurrent_connections')} threads")

def example_post_test_hook(results: dict):
    """Example: Print test summary."""
    total_queries = results.get('total_queries', 0)
    duration = results.get('total_duration', 0)
    logger.info(f"Test completed: {total_queries} queries in {duration:.2f}s")
