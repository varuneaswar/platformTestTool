from typing import Dict, Any
import logging

class NonRelationalConnection:
    """Manages non-relational database connections (MongoDB, Redis)."""
    def __init__(self):
        self.clients = {}
        self.logger = logging.getLogger(__name__)

    def create_connection(self, conn_id: str, config: Dict[str, Any]) -> bool:
        db_type = config.get('db_type', '').lower()
        try:
            if db_type == 'mongodb':
                from pymongo import MongoClient
                uri = config.get('uri')
                if not uri:
                    host = config.get('host', '127.0.0.1')
                    port = config.get('port', 27017)
                    database = config.get('database', '')
                    username = config.get('username')
                    password = config.get('password')
                    if username is not None and password is not None:
                        base = f"mongodb://{username}:{password}@{host}:{port}"
                    else:
                        base = f"mongodb://{host}:{port}"
                    uri = f"{base}/{database}" if database else base
                client = MongoClient(uri)
                # Test connection
                client.admin.command('ping')
                self.clients[conn_id] = client
            elif db_type == 'redis':
                import redis
                client = redis.Redis(host=config['host'], port=config['port'], password=config.get('password'))
                client.ping()
                self.clients[conn_id] = client
            else:
                raise ValueError(f"Unsupported non-relational db type: {db_type}")
            self.logger.info(f"Successfully created non-relational connection: {conn_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create non-relational connection {conn_id}: {str(e)}")
            return False

    def get_connection(self, conn_id: str):
        if conn_id not in self.clients:
            raise KeyError(f"Connection {conn_id} does not exist")
        return self.clients[conn_id]

    def close_connection(self, conn_id: str) -> bool:
        try:
            if conn_id in self.clients:
                # MongoClient and Redis don't need explicit close, but we can delete
                del self.clients[conn_id]
                self.logger.info(f"Successfully closed non-relational connection: {conn_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error closing non-relational connection {conn_id}: {str(e)}")
            return False

    def close_all_connections(self):
        self.clients.clear()
