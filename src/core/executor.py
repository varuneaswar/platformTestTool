from abc import ABC, abstractmethod
from typing import Dict, Any, Sequence

class Executor(ABC):
    """Abstract executor: single query or batch executions return a structured result dict."""
    
    @abstractmethod
    def execute(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute single query dict and return result dict (duration, success, rows, error, etc.)."""
        pass

    @abstractmethod
    def execute_batch(self, queries: Sequence[Dict[str, Any]]) -> Sequence[Dict[str, Any]]:
        """Execute a batch of queries and return list of result dicts."""
        pass
