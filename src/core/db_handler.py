from abc import ABC, abstractmethod

# Registry for handlers
db_handler_registry = {}

def register_db_handler(db_type):
    def decorator(cls):
        db_handler_registry[db_type.lower()] = cls
        return cls
    return decorator

def get_db_handler(db_type):
    handler_cls = db_handler_registry.get(db_type.lower())
    if not handler_cls:
        raise ValueError(f"No handler registered for db_type: {db_type}")
    return handler_cls()

class DatabaseHandler(ABC):
    @abstractmethod
    def connect(self, user_id, db_config):
        pass

    @abstractmethod
    def get_executor(self, user_id):
        pass

    @abstractmethod
    def close(self):
        pass

# Example PostgreSQL handler
from .connection import DatabaseConnection
from .sqlalchemy_executor import SQLAlchemyExecutor

@register_db_handler('postgresql')
class PostgresHandler(DatabaseHandler):
    def __init__(self):
        self.db_conn = DatabaseConnection()
        self.executor = None

    def connect(self, user_id, db_config):
        self.db_conn.create_connection(user_id, db_config)
        engine = self.db_conn.get_connection(user_id)
        self.executor = SQLAlchemyExecutor(engine)

    def get_executor(self, user_id):
        return self.executor

    def close(self):
        self.db_conn.close_all_connections()

# MySQL handler
@register_db_handler('mysql')
class MySQLHandler(DatabaseHandler):
    def __init__(self):
        self.db_conn = DatabaseConnection()
        self.executor = None

    def connect(self, user_id, db_config):
        self.db_conn.create_connection(user_id, db_config)
        engine = self.db_conn.get_connection(user_id)
        self.executor = SQLAlchemyExecutor(engine)

    def get_executor(self, user_id):
        return self.executor

    def close(self):
        self.db_conn.close_all_connections()

# MS SQL Server handler
@register_db_handler('mssql')
class MSSQLHandler(DatabaseHandler):
    def __init__(self):
        self.db_conn = DatabaseConnection()
        self.executor = None

    def connect(self, user_id, db_config):
        self.db_conn.create_connection(user_id, db_config)
        engine = self.db_conn.get_connection(user_id)
        self.executor = SQLAlchemyExecutor(engine)

    def get_executor(self, user_id):
        return self.executor

    def close(self):
        self.db_conn.close_all_connections()

# Oracle handler
@register_db_handler('oracle')
class OracleHandler(DatabaseHandler):
    def __init__(self):
        self.db_conn = DatabaseConnection()
        self.executor = None

    def connect(self, user_id, db_config):
        self.db_conn.create_connection(user_id, db_config)
        engine = self.db_conn.get_connection(user_id)
        self.executor = SQLAlchemyExecutor(engine)

    def get_executor(self, user_id):
        return self.executor

    def close(self):
        self.db_conn.close_all_connections()

# Example MongoDB handler (stub, expand as needed)
try:
    from .connection_nonrel import NonRelationalConnection
except ImportError:
    NonRelationalConnection = None

@register_db_handler('mongodb')
class MongoHandler(DatabaseHandler):
    def __init__(self):
        self.nonrel_conn = NonRelationalConnection() if NonRelationalConnection else None
        self.client = None

    def connect(self, user_id, db_config):
        if self.nonrel_conn:
            self.nonrel_conn.create_connection(user_id, db_config)
            self.client = self.nonrel_conn.get_connection(user_id)

    def get_executor(self, user_id):
        return self.client  # For Mongo, you may use the client directly

    def close(self):
        pass  # Implement if needed
