from typing import Dict, Any
import os
from dotenv import load_dotenv
import json
import logging

class Settings:
    """Manages configuration settings for the soak testing framework."""
    
    def __init__(self, config_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.config: Dict[str, Any] = {}
        self.load_env()
        if config_path:
            self.load_config(config_path)

    def load_env(self):
        """Load environment variables from .env file."""
        load_dotenv()

    def load_config(self, config_path: str):
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            self.logger.info(f"Successfully loaded configuration from {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            raise

    def get_database_config(self, connection_id: str, user_db_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get database connection configuration with environment variable support.
        
        This method supports two modes:
        1. Centralized databases config: Load from config['databases'][connection_id]
        2. Inline user config: Use provided user_db_config with env var overrides
        
        Args:
            connection_id: Identifier for the database connection (used for env var prefix)
            user_db_config: Optional inline database config from user config
            
        Returns:
            Dictionary containing database connection parameters
        """
        # Start with user-provided config or fetch from centralized databases section
        if user_db_config is not None:
            db_config = user_db_config.copy()
        elif 'databases' in self.config and connection_id in self.config['databases']:
            db_config = self.config['databases'][connection_id].copy()
        else:
            # If no config provided, try to build entirely from environment variables
            db_config = {}
            
        # Override with environment variables if they exist
        env_prefix = f"DB_{connection_id.upper()}_"
        
        # Get db_type from environment or config
        db_type = os.getenv(f"{env_prefix}TYPE", db_config.get('db_type'))
        if db_type:
            db_config['db_type'] = db_type
            
        # Common database connection parameters
        if os.getenv(f"{env_prefix}HOST"):
            db_config['host'] = os.getenv(f"{env_prefix}HOST")
        if os.getenv(f"{env_prefix}PORT"):
            db_config['port'] = int(os.getenv(f"{env_prefix}PORT"))
        if os.getenv(f"{env_prefix}NAME"):
            db_config['database'] = os.getenv(f"{env_prefix}NAME")
        if os.getenv(f"{env_prefix}USER"):
            db_config['username'] = os.getenv(f"{env_prefix}USER")
        if os.getenv(f"{env_prefix}PASSWORD"):
            db_config['password'] = os.getenv(f"{env_prefix}PASSWORD")
            
        # Oracle-specific service_name parameter
        if os.getenv(f"{env_prefix}SERVICE_NAME"):
            db_config['service_name'] = os.getenv(f"{env_prefix}SERVICE_NAME")
            
        return db_config

    def get_test_config(self) -> Dict[str, Any]:
        """
        Get test execution configuration.
        
        Returns:
            Dictionary containing test configuration parameters
        """
        test_config = self.config.get('test_config', {})
        
        # Override with environment variables
        test_config.update({
            'concurrent_connections': int(os.getenv('TEST_CONCURRENT_CONNECTIONS', 
                                                  test_config.get('concurrent_connections', 5))),
            'queries_per_connection': int(os.getenv('TEST_QUERIES_PER_CONNECTION',
                                                  test_config.get('queries_per_connection', 100))),
            'execution_time': int(os.getenv('TEST_EXECUTION_TIME',
                                          test_config.get('execution_time', 3600))),
            'ramp_up_time': int(os.getenv('TEST_RAMP_UP_TIME',
                                         test_config.get('ramp_up_time', 300))),
            'metrics_interval': int(os.getenv('TEST_METRICS_INTERVAL',
                                            test_config.get('metrics_interval', 60)))
        })
        
        return test_config

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Dictionary containing logging configuration parameters
        """
        log_config = self.config.get('logging', {})
        
        # Override with environment variables
        log_config.update({
            'level': os.getenv('LOG_LEVEL', log_config.get('level', 'INFO')),
            'file': os.getenv('LOG_FILE', log_config.get('file', 'soak_test.log')),
            'format': os.getenv('LOG_FORMAT', log_config.get('format',
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        })
        
        return log_config

    def save_config(self, config_path: str):
        """
        Save current configuration to a file.
        
        Args:
            config_path: Path to save the configuration file
        """
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Successfully saved configuration to {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            raise

    def update_config(self, updates: Dict[str, Any]):
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary containing configuration updates
        """
        def deep_update(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
            for k, v in u.items():
                if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
            return d
            
        self.config = deep_update(self.config, updates)
        self.logger.info("Configuration updated successfully")