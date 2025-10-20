import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path
from typing import Dict, Any

class LoggingUtils:
    """Utility class for setting up logging configuration."""
    
    @staticmethod
    def setup_logging(config: Dict[str, Any]):
        """
        Set up logging configuration for the application.
        
        Args:
            config: Dictionary containing logging configuration
                Required keys:
                - level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                - file: Log file path
                - format: Log message format
        """
        log_level = getattr(logging, config['level'].upper(), logging.INFO)
        log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_file = config.get('file', 'soak_test.log')
        
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Setup file handler with rotation
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Log initial setup
        root_logger.info("Logging setup completed")
        
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger instance with the specified name.
        
        Args:
            name: Name for the logger (typically __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
        
    @staticmethod
    def set_level(level: str):
        """
        Set logging level for the root logger.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)