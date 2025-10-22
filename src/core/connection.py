from typing import Dict, Any
import sqlalchemy
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import logging

class DatabaseConnection:
    """Manages database connections for different database types."""
    
    def __init__(self):
        self.engines = {}
        self.logger = logging.getLogger(__name__)

    def create_connection(self, conn_id: str, config: Dict[str, Any]) -> bool:
        """
        Create a new database connection.
        
        Args:
            conn_id: Unique identifier for the connection
            config: Dictionary containing connection parameters
                Required keys:
                - db_type: Type of database (mysql, postgresql, mssql, oracle)
                - host: Database host
                - port: Database port
                - database: Database name (or service_name for Oracle)
                - username: Database username
                - password: Database password
                Optional keys for Oracle:
                - service_name: Oracle service name (defaults to database value)
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            db_type = config.get('db_type', '').lower()
            connection_url = self._build_connection_url(db_type, config)
            engine = create_engine(connection_url)
            
            # Test the connection (use text() for SQLAlchemy 2.x)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.engines[conn_id] = engine
            self.logger.info(f"Successfully created connection: {conn_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create connection {conn_id}: {str(e)}")
            return False

    def _build_connection_url(self, db_type: str, config: Dict[str, Any]) -> str:
        """Build database connection URL based on database type and configuration."""
        username = config.get('username', '')
        password = quote_plus(config.get('password', ''))
        host = config.get('host', '')
        port = config.get('port', '')
        database = config.get('database', '')
        
        if db_type == 'postgresql':
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'mysql':
            return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'mssql':
            return f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_type == 'oracle':
            # Oracle connection using oracledb driver
            # Format: oracle+oracledb://user:pass@host:port/?service_name=service
            service_name = config.get('service_name', database)
            return f"oracle+oracledb://{username}:{password}@{host}:{port}/?service_name={service_name}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def get_connection(self, conn_id: str) -> sqlalchemy.engine.Engine:
        """Get an existing database connection."""
        if conn_id not in self.engines:
            raise KeyError(f"Connection {conn_id} does not exist")
        return self.engines[conn_id]

    def close_connection(self, conn_id: str) -> bool:
        """Close a specific database connection."""
        try:
            if conn_id in self.engines:
                self.engines[conn_id].dispose()
                del self.engines[conn_id]
                self.logger.info(f"Successfully closed connection: {conn_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error closing connection {conn_id}: {str(e)}")
            return False

    def close_all_connections(self):
        """Close all database connections."""
        for conn_id in list(self.engines.keys()):
            self.close_connection(conn_id)