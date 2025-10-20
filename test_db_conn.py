from src.core.db_handler import get_db_handler

# Test if handler has db_conn attribute
handler = get_db_handler('postgresql')
print(f'Handler: {handler}')
print(f'Handler type: {type(handler).__name__}')

# Connect
handler.connect('test', {
    'host': '127.0.0.1',
    'port': 5432,
    'database': 'postgres',
    'username': 'postgres',
    'password': 'admin'
})

# Check db_conn
db_conn = getattr(handler, 'db_conn', None)
print(f'db_conn: {db_conn}')
print(f'db_conn is None: {db_conn is None}')

# If db_conn exists, try to get connection
if db_conn:
    try:
        engine = db_conn.get_connection('test')
        print(f'Engine: {engine}')
        print('SUCCESS: db_conn is available and working')
    except Exception as e:
        print(f'ERROR getting connection: {e}')
else:
    print('ERROR: db_conn is None!')
