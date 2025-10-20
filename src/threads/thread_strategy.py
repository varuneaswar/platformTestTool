from abc import ABC, abstractmethod
from typing import Dict, List

class ThreadAssignmentStrategy(ABC):
    """Abstract base for thread assignment strategies."""
    
    @abstractmethod
    def assign_threads(self, config: dict) -> Dict[str, List[str]]:
        """
        Assign threads to operations based on strategy.
        
        Returns:
            Dict mapping operation keys to list of thread IDs
            Example: {
                'read_select_simple': ['thread_0', 'thread_1'],
                'write_insert_simple': ['thread_2']
            }
        """
        pass

class FixedCountStrategy(ThreadAssignmentStrategy):
    """Assign fixed number of threads to each operation type."""
    
    def assign_threads(self, config: dict) -> Dict[str, List[str]]:
        total_threads = config.get('concurrent_connections', 10)
        read_ratio = config.get('read_ratio', 0.7)
        write_ratio = config.get('write_ratio', 0.3)
        
        # Calculate thread counts
        read_threads = int(total_threads * read_ratio)
        write_threads = total_threads - read_threads
        
        # Distribute read threads
        assignments = {}
        thread_id = 0
        
        # Read operations
        read_ops = ['read_select_simple', 'read_select_medium', 'read_select_complex']
        threads_per_read_op = max(1, read_threads // len(read_ops))
        
        for op in read_ops:
            thread_list = []
            for _ in range(threads_per_read_op):
                thread_list.append(f"thread_{thread_id}")
                thread_id += 1
            assignments[op] = thread_list
        
        # Write operations
        write_ops = [
            'write_insert_simple', 'write_insert_medium', 'write_insert_complex',
            'write_update_simple', 'write_update_medium', 'write_update_complex',
            'write_delete_simple', 'write_delete_medium', 'write_delete_complex'
        ]
        threads_per_write_op = max(1, write_threads // len(write_ops))
        
        for op in write_ops:
            thread_list = []
            for _ in range(threads_per_write_op):
                if thread_id < total_threads:
                    thread_list.append(f"thread_{thread_id}")
                    thread_id += 1
            if thread_list:  # Only add if threads assigned
                assignments[op] = thread_list
        
        return assignments

class WeightedStrategy(ThreadAssignmentStrategy):
    """Assign threads based on custom weights per operation."""
    
    def assign_threads(self, config: dict) -> Dict[str, List[str]]:
        total_threads = config.get('concurrent_connections', 10)
        weights = config.get('operation_weights', {})
        
        # Default weights if not specified
        default_weights = {
            'read_select_simple': 3,
            'read_select_medium': 2,
            'read_select_complex': 1,
            'write_insert_simple': 2,
            'write_update_simple': 1,
            'write_delete_simple': 1
        }
        
        weights = {**default_weights, **weights}
        
        # Calculate total weight
        total_weight = sum(weights.values())
        
        # Assign threads proportionally
        assignments = {}
        thread_id = 0
        
        for op, weight in weights.items():
            thread_count = max(1, int((weight / total_weight) * total_threads))
            thread_list = []
            
            for _ in range(thread_count):
                if thread_id < total_threads:
                    thread_list.append(f"thread_{thread_id}")
                    thread_id += 1
            
            if thread_list:
                assignments[op] = thread_list
        
        return assignments

def get_strategy(strategy_name: str = 'fixed') -> ThreadAssignmentStrategy:
    """Factory function to get thread assignment strategy."""
    strategies = {
        'fixed': FixedCountStrategy,
        'weighted': WeightedStrategy
    }
    
    strategy_class = strategies.get(strategy_name, FixedCountStrategy)
    return strategy_class()
