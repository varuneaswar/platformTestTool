import json
import os
from typing import Optional, Dict, Any

class ConfigLoader:
    """Load configuration from JSON or YAML files."""
    
    def __init__(self, default_config_path: Optional[str] = None):
        self.default_path = default_config_path
        self.yaml_available = False
        
        # Try to import yaml support
        try:
            import yaml
            self.yaml = yaml
            self.yaml_available = True
        except ImportError:
            self.yaml = None
    
    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_path: Path to config file. If None, use default_path.
        
        Returns:
            Configuration dictionary
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file format is not supported or invalid
        """
        path = config_path or self.default_path
        
        if not path:
            raise ValueError("No configuration file path provided")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        # Determine file type by extension
        _, ext = os.path.splitext(path)
        ext = ext.lower()
        
        if ext == '.json':
            return self._load_json(path)
        elif ext in ['.yaml', '.yml']:
            return self._load_yaml(path)
        else:
            raise ValueError(f"Unsupported config file format: {ext}")
    
    def _load_json(self, path: str) -> Dict[str, Any]:
        """Load JSON configuration file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not isinstance(config, dict):
                raise ValueError("Config file must contain a JSON object")
            
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        if not self.yaml_available:
            raise ValueError("YAML support not available. Install PyYAML: pip install pyyaml")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = self.yaml.safe_load(f)
            
            if not isinstance(config, dict):
                raise ValueError("Config file must contain a YAML mapping/object")
            
            return config
        except Exception as e:
            raise ValueError(f"Error loading YAML config: {e}")
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration has required fields.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['database_type', 'connection_params']
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Required config field missing: {field}")
        
        # Validate connection params
        conn_params = config['connection_params']
        if not isinstance(conn_params, dict):
            raise ValueError("connection_params must be an object/dictionary")
        
        # Database-specific validation
        db_type = config['database_type'].lower()
        
        if db_type == 'postgresql':
            required_conn_fields = ['host', 'port', 'database', 'user', 'password']
            for field in required_conn_fields:
                if field not in conn_params:
                    raise ValueError(f"Required connection parameter missing: {field}")
        
        elif db_type == 'mongodb':
            if 'uri' not in conn_params and 'host' not in conn_params:
                raise ValueError("MongoDB requires either 'uri' or 'host' in connection_params")
        
        return True
    
    def load_and_validate(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load and validate configuration file."""
        config = self.load(config_path)
        self.validate_config(config)
        return config
