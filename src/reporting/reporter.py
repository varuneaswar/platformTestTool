from abc import ABC, abstractmethod
from typing import Dict, Any

class Reporter(ABC):
    """Abstract reporter interface for recording metrics."""
    
    @abstractmethod
    def record(self, metric: Dict[str, Any]) -> None:
        """Record a single metric."""
        pass

    @abstractmethod
    def finalize(self) -> None:
        """Flush, write files or commit DB transactions."""
        pass
