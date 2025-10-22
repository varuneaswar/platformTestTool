from src.core.connection import DatabaseConnection
from src.core.query_executor import QueryExecutor
from src.core.performance_metrics import PerformanceMetrics
from src.config.settings import Settings
from src.utils.logging_utils import LoggingUtils
from src.utils.metrics_utils import MetricsUtils
import time
import secrets
import string
import json
from concurrent.futures import ThreadPoolExecutor



def run_user_soak(user_config):
    # Helper to insert metrics into soak_test_metrics table
    from sqlalchemy import text
    def insert_metric_to_db(metric, db_conn, conn_id, db_type):
        from sqlalchemy import text
        try:
            engine = db_conn.get_connection(conn_id)
            with engine.begin() as conn:
                # Use database-specific timestamp conversion
                if db_type == 'oracle':
                    # Oracle uses TO_TIMESTAMP with FROM_TZ for epoch conversion
                    timestamp_func = "TO_TIMESTAMP('1970-01-01 00:00:00', 'YYYY-MM-DD HH24:MI:SS') + NUMTODSINTERVAL(:start_time, 'SECOND')"
                    timestamp_func_end = "TO_TIMESTAMP('1970-01-01 00:00:00', 'YYYY-MM-DD HH24:MI:SS') + NUMTODSINTERVAL(:end_time, 'SECOND')"
                elif db_type == 'mssql':
                    # SQL Server uses DATEADD with epoch
                    timestamp_func = "DATEADD(second, :start_time, '1970-01-01 00:00:00')"
                    timestamp_func_end = "DATEADD(second, :end_time, '1970-01-01 00:00:00')"
                elif db_type == 'mysql':
                    # MySQL uses FROM_UNIXTIME
                    timestamp_func = "FROM_UNIXTIME(:start_time)"
                    timestamp_func_end = "FROM_UNIXTIME(:end_time)"
                else:
                    # PostgreSQL and others use to_timestamp
                    timestamp_func = "to_timestamp(:start_time)"
                    timestamp_func_end = "to_timestamp(:end_time)"
                
                insert_sql = text(f'''
                    INSERT INTO soak_test_metrics (
                        job_id, test_case_id, start_time, end_time, duration, success, error, rows_affected, memory_usage, cpu_time,
                        query_gist, file_name, operation, complexity, thread_name, return_code, error_code, error_desc, rows_processed
                    ) VALUES (
                        :job_id, :test_case_id, {timestamp_func}, {timestamp_func_end}, :duration, :success, :error, :rows_affected, :memory_usage, :cpu_time,
                        :query_gist, :file_name, :operation, :complexity, :thread_name, :return_code, :error_code, :error_desc, :rows_processed
                    )
                ''')
                # Extract fields from metric and query_id for fallback
                parts = metric['query_id'].split('_')
                test_case_id = metric.get('test_case_id') or (parts[1] if len(parts) > 1 else '')
                # Always use {test_type}_{logical_thread} for thread_name
                logical_thread = ''
                if 'thread_name' in metric and metric['thread_name']:
                    if metric['thread_name'].startswith('soaktest_') or metric['thread_name'].startswith('loadtest_'):
                        thread_name = metric['thread_name']
                    else:
                        logical_thread = metric['thread_name'].split('_', 1)[-1]
                        thread_name = f"{test_type}_{logical_thread}"
                else:
                    thread_name = f"{test_type}_thread"
                operation = metric.get('operation') or (parts[5] if len(parts) > 5 else '')
                complexity = metric.get('complexity') or (parts[6] if len(parts) > 6 else '')
                file_name = metric.get('file_name', '')
                params = {
                    'job_id': metric.get('job_id', ''),
                    'test_case_id': test_case_id,
                    'start_time': metric.get('start_time', 0),
                    'end_time': metric.get('end_time', 0),
                    'duration': metric.get('duration', 0),
                    'success': metric.get('success', False),
                    'error': metric.get('error', ''),
                    'rows_affected': metric.get('rows_affected', 0),
                    'memory_usage': metric.get('memory_usage', 0),
                    'cpu_time': metric.get('cpu_time', 0),
                    'query_gist': (metric.get('query', '') or '')[:200],
                    'file_name': file_name,
                    'operation': operation,
                    'complexity': complexity,
                    'thread_name': thread_name,
                    'return_code': metric.get('return_code', ''),
                    'error_code': metric.get('error_code', ''),
                    'error_desc': metric.get('error', ''),
                    'rows_processed': metric.get('rows_affected', 0)
                }
                conn.execute(insert_sql, params)
        except Exception as e:
            print(f"DB insert failed: {e}. Params: {metric}")
    # Generate unique 24-char alphanumeric job_id
    job_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
    import os
    from datetime import datetime
    
    user_id = user_config['user_id']
    test_config = user_config['test_config']
    
    # Support for database_ref to reference centralized database configs
    # Load environment variables first
    from src.config.settings import Settings
    settings_loader = Settings(None)
    settings_loader.load_env()
    
    if 'database_ref' in user_config:
        # Load database config from centralized config or environment
        db_ref = user_config['database_ref']
        db_config = settings_loader.get_database_config(db_ref)
    else:
        # Use inline database config with environment variable overrides
        db_config = user_config['database']
        # Apply environment variable overrides using the user_id as connection_id
        db_config = settings_loader.get_database_config(user_id, db_config)
    
    db_type = db_config.get('db_type', 'unknown').lower()
    db_user = db_config.get('username', 'unknown')
    single_run_mode_val = str(test_config.get('single_run_mode', 'per_thread'))
    if single_run_mode_val == 'per_thread':
        test_type = 'soaktest'
    elif single_run_mode_val == 'per_query_once':
        test_type = 'loadtest'
    else:
        test_type = single_run_mode_val
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    folder_base = f"{db_type}_{test_type}_{db_user}_{job_id}_{timestamp}"
    # Helper to build thread_name for metrics
    def build_thread_name(logical_thread):
        # Only use the operation/complexity part, not the config/test name
        if logical_thread.startswith('read_'):
            suffix = logical_thread[len('read_'):]
        elif logical_thread.startswith('write_'):
            suffix = logical_thread[len('write_'):]
        else:
            suffix = logical_thread
        return f"{test_type}_{suffix}"
    log_file = f"logs/{folder_base}.log"
    result_folder = f"reports/{folder_base}/"
    os.makedirs(result_folder, exist_ok=True)
    html_report_name = f"test_report_{test_type}_{db_user}_{job_id}.html"
    csv_report_name = f"query_metrics_report_{test_type}_{db_user}_{job_id}.csv"
    json_report_name = f"metrics_{test_type}_{db_user}_{job_id}.json"
    # Update logger to use unique log file
    LoggingUtils.setup_logging({"file": log_file, "level": "INFO"})
    import threading
    import queue
    duration = test_config['execution_time']
    # Single run mode: 'per_thread' (default: fixed runs per thread) or 'per_query_once' (each query file executed once)
    single_run_mode = str(test_config.get('single_run_mode', 'per_thread'))
    # Auto-enable single_run_flag when execution_time is 0 OR when explicitly set
    single_run_flag = bool(test_config.get('single_run_on_zero_or_missing_duration', duration == 0))
    queries_per_connection = int(test_config.get('queries_per_connection', 10))
    # Retry configuration: control number of retries and whether to skip non-relational DBs
    retry_cfg = test_config.get('retry', {}) if isinstance(test_config.get('retry', {}), dict) else {}
    retry_enabled = bool(retry_cfg.get('enabled', False))
    retry_count = int(retry_cfg.get('retries', 1))
    retry_skip_nonrelational = bool(retry_cfg.get('skip_nonrelational', True))
    query_folder = user_config.get('query_folder', '')
    thread_ratios = user_config.get('thread_ratios', {})
    queue_settings = user_config.get('queue_settings', {"replenish_interval": 10, "max_queue_size": 1000})

    logger = LoggingUtils.get_logger(f"user_{user_id}")
    metrics = PerformanceMetrics()

    # Use extensible handler abstraction
    from src.core.db_handler import get_db_handler
    try:
        handler = get_db_handler(db_type)
    except Exception as e:
        logger.error(f"[{user_id}] {str(e)}")
        return
    handler.connect(user_id, db_config)
    executor = handler.get_executor(user_id)
    db_conn = getattr(handler, 'db_conn', None)
    nonrel_client = getattr(handler, 'client', None)

    # Thread pool setup
    total_threads = test_config.get('concurrent_connections', 2)
    read_threads = int(total_threads * thread_ratios.get('read', 0.5))
    write_threads = total_threads - read_threads

    # Complexity ratios
    read_complexity = thread_ratios.get('read_complexity', {"simple": 1.0})
    write_ops = thread_ratios.get('write_operations', {"insert": 1.0})
    write_complexity = thread_ratios.get('write_complexity', {"simple": 1.0})

    # Prepare thread assignments
    thread_assignments = []
    # Read threads split by complexity
    for op, ratio in read_complexity.items():
        n_threads = int(read_threads * ratio)
        for _ in range(n_threads):
            thread_assignments.append({"type": "read", "complexity": op})
    # Write threads split by operation and complexity
    for op, op_ratio in write_ops.items():
        for cx, cx_ratio in write_complexity.items():
            n_threads = int(write_threads * op_ratio * cx_ratio)
            for _ in range(n_threads):
                thread_assignments.append({"type": "write", "operation": op, "complexity": cx})

    if not thread_assignments:
        thread_assignments = [{"type": "read", "complexity": "simple"} for _ in range(total_threads)]

    logger.info(f"[{user_id}] Thread assignments: {thread_assignments}")

    # Queue management: create queues for each operation/complexity
    queue_map = {}
    for thread_info in thread_assignments:
        if thread_info["type"] == "read":
            key = f"read_{thread_info['complexity']}"
        else:
            key = f"write_{thread_info['operation']}_{thread_info['complexity']}"
        if key not in queue_map:
            queue_map[key] = queue.Queue(maxsize=queue_settings["max_queue_size"])

    # Query file loader
    import glob
    import os
    def get_queries_for_queue(key):
        db_type_local = str(db_config.get('db_type', '')).lower()
        base_folder = query_folder
        queries = []

        # Helper to load JSON/JSON5 content
        def load_json_like(path):
            import json
            if path.lower().endswith('.json5'):
                try:
                    import json5  # type: ignore
                    with open(path, 'r', encoding='utf-8') as f:
                        return json5.load(f)
                except ImportError:
                    # Fallback: try to parse with json (may fail on json5 features)
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)

        # Determine folder and file patterns based on db type and key
        if db_type_local == 'mongodb':
            # For MongoDB: folder structure base/<operation>/<complexity>, files: .json or .json5
            if key.startswith("read"):
                # read_{complexity} -> find/<complexity>
                _, complexity = key.split('_', 1)
                folder = os.path.join(base_folder, 'find', complexity)
            else:
                # write_{operation}_{complexity} -> <operation>/<complexity>
                _, operation, complexity = key.split('_', 2)
                folder = os.path.join(base_folder, operation, complexity)

            patterns = [os.path.join(folder, '*.json'), os.path.join(folder, '*.json5')]
            for pattern in patterns:
                for file in glob.glob(pattern):
                    try:
                        payload = load_json_like(file)
                        if not isinstance(payload, dict):
                            continue
                        action = str(payload.get('action', '')).lower()
                        collection = payload.get('collection', '')
                        # Map to reporting operation categories
                        if action == 'find':
                            operation_rep = 'select'
                        elif action.startswith('insert'):
                            operation_rep = 'insert'
                        elif action.startswith('update'):
                            operation_rep = 'update'
                        elif action.startswith('delete'):
                            operation_rep = 'delete'
                        else:
                            operation_rep = action or ('select' if key.startswith('read') else 'unknown')

                        # Derive complexity from folder
                        complexity = os.path.basename(os.path.dirname(file))

                        # Construct query dict for execution and reporting
                        q = {
                            'file_name': os.path.basename(file),
                            'operation': operation_rep,
                            'complexity': complexity,
                            'action': action or ('find' if key.startswith('read') else ''),
                            'collection': collection,
                        }
                        # Include common parameters if provided
                        for k in ('filter', 'projection', 'update', 'document', 'documents', 'limit', 'sort', 'upsert'):
                            if k in payload:
                                q[k] = payload[k]
                        # Store a stringified gist for display
                        try:
                            import json as _json
                            q['query'] = _json.dumps(payload)[:1000]
                        except Exception:
                            q['query'] = str(payload)
                        queries.append(q)
                    except Exception:
                        continue
        else:
            # Relational DBs (existing behavior): .sql files under read/select/<complexity> and write/<op>/<complexity>
            if key.startswith("read"):
                # read_{complexity}
                _, complexity = key.split('_', 1)
                folder = os.path.join(base_folder, 'read', 'select', complexity)
            else:
                # write_{operation}_{complexity}
                _, operation, complexity = key.split('_', 2)
                folder = os.path.join(base_folder, 'write', operation, complexity)
            for file in glob.glob(os.path.join(folder, '*.sql')):
                try:
                    with open(file, 'r') as f:
                        sql = f.read().strip()
                        if sql and not sql.startswith('--'):
                            # Attach file_name and operation/complexity for reporting
                            query_info = {
                                "query": sql,
                                "file_name": os.path.basename(file)
                            }
                            # Optionally, parse operation/complexity from key
                            if key.startswith("read"):
                                query_info["operation"] = "select"
                                query_info["complexity"] = key.split('_', 1)[1]
                            else:
                                _, operation, complexity = key.split('_', 2)
                                query_info["operation"] = operation
                                query_info["complexity"] = complexity
                            queries.append(query_info)
                except Exception:
                    continue

        # Fallback if no queries found
        if not queries:
            if key.startswith("read"):
                _, complexity = key.split('_', 1)
                if db_type_local == 'mongodb':
                    queries = [{
                        'file_name': 'default.json',
                        'operation': 'select',
                        'complexity': complexity,
                        'action': 'find',
                        'collection': 'test',
                        'filter': {},
                        'query': '{"action":"find","collection":"test","filter":{}}'
                    }]
                else:
                    queries = [{
                        "query": "SELECT current_date",
                        "file_name": "default.sql",
                        "operation": "select",
                        "complexity": complexity
                    }]
            else:
                _, operation, complexity = key.split('_', 2)
                if db_type_local == 'mongodb':
                    # Provide a minimal default write op
                    if operation == 'insert':
                        queries = [{
                            'file_name': 'default.json',
                            'operation': 'insert',
                            'complexity': complexity,
                            'action': 'insert_one',
                            'collection': 'test',
                            'document': {'_sample': True},
                            'query': '{"action":"insert_one","collection":"test","document":{"_sample":true}}'
                        }]
                    elif operation == 'update':
                        queries = [{
                            'file_name': 'default.json',
                            'operation': 'update',
                            'complexity': complexity,
                            'action': 'update_many',
                            'collection': 'test',
                            'filter': {},
                            'update': {'$set': {'_updated': True}},
                            'query': '{"action":"update_many","collection":"test","filter":{},"update":{"$set":{"_updated":true}}}'
                        }]
                    elif operation == 'delete':
                        queries = [{
                            'file_name': 'default.json',
                            'operation': 'delete',
                            'complexity': complexity,
                            'action': 'delete_many',
                            'collection': 'test',
                            'filter': {},
                            'query': '{"action":"delete_many","collection":"test","filter":{}}'
                        }]
                    else:
                        queries = []
                else:
                    queries = [{
                        "query": "SELECT version()",
                        "file_name": "default.sql",
                        "operation": operation,
                        "complexity": complexity
                    }]
        return queries

    # Queue replenisher
    def replenish_queues():
        for key, q in queue_map.items():
            while not q.full():
                for query in get_queries_for_queue(key):
                    try:
                        q.put_nowait(query)
                    except queue.Full:
                        break

    # Initial fill
    if duration == 0 and single_run_flag and single_run_mode == 'per_query_once':
        # For per_query_once mode, only add each query once (no duplication)
        for key, q in queue_map.items():
            for query in get_queries_for_queue(key):
                try:
                    q.put_nowait(query)
                except queue.Full:
                    break
    else:
        # For time-based or per_thread mode, fill queues to capacity
        replenish_queues()

    # Thread runner
    def thread_runner(thread_info):
        local_count = 0
        start_time = time.time()
        if thread_info["type"] == "read":
            key = f"read_{thread_info['complexity']}"
        else:
            key = f"write_{thread_info['operation']}_{thread_info['complexity']}"
        q = queue_map[key]

        # Helper to ensure query dict has expected metadata
        def prepare_query(qobj):
            if isinstance(qobj, dict):
                if 'operation' not in qobj or not qobj['operation']:
                    if thread_info['type'] == 'read':
                        qobj['operation'] = 'select'
                    else:
                        qobj['operation'] = thread_info.get('operation', '')
                if 'complexity' not in qobj or not qobj['complexity']:
                    qobj['complexity'] = thread_info.get('complexity', '')
                if 'file_name' not in qobj or not qobj['file_name']:
                    qobj['file_name'] = 'unknown.sql'
            return qobj

        # Process a single query object: execute, optionally retry, record metrics
        def process_query(query, local_count, i_index=0):
            nonlocal metrics, db_type, db_conn, executor
            query = prepare_query(query)
            results = []
            if db_type in ['mongodb', 'redis']:
                # Non-relational execution with timing and row counts
                try:
                    if db_type == 'mongodb':
                        collection = query.get('collection')
                        action = str(query.get('action', '')).lower()
                        if not collection or not action:
                            raise ValueError("MongoDB query requires 'collection' and 'action'")
                        col = nonrel_client[collection]
                        t0 = time.time()
                        rows_affected = 0
                        error = None
                        success = True
                        if action == 'find':
                            filt = query.get('filter', {})
                            proj = query.get('projection')
                            cur = col.find(filt, projection=proj)
                            if 'sort' in query and query['sort']:
                                cur = cur.sort(query['sort'])
                            if 'limit' in query and query['limit']:
                                cur = cur.limit(int(query['limit']))
                            data = list(cur)
                            rows_affected = len(data)
                        elif action == 'insert_one':
                            doc = query.get('document') or {}
                            r = col.insert_one(doc)
                            rows_affected = 1 if getattr(r, 'acknowledged', True) else 0
                        elif action == 'insert_many':
                            docs = query.get('documents') or []
                            r = col.insert_many(docs)
                            rows_affected = len(getattr(r, 'inserted_ids', []) or [])
                        elif action == 'update_one':
                            filt = query.get('filter', {})
                            upd = query.get('update') or {}
                            r = col.update_one(filt, upd, upsert=bool(query.get('upsert', False)))
                            rows_affected = getattr(r, 'modified_count', 0)
                        elif action == 'update_many':
                            filt = query.get('filter', {})
                            upd = query.get('update') or {}
                            r = col.update_many(filt, upd, upsert=bool(query.get('upsert', False)))
                            rows_affected = getattr(r, 'modified_count', 0)
                        elif action == 'delete_one':
                            filt = query.get('filter', {})
                            r = col.delete_one(filt)
                            rows_affected = getattr(r, 'deleted_count', 0)
                        elif action == 'delete_many':
                            filt = query.get('filter', {})
                            r = col.delete_many(filt)
                            rows_affected = getattr(r, 'deleted_count', 0)
                        else:
                            raise ValueError(f"Unsupported MongoDB action: {action}")

                        t1 = time.time()
                        results = [{
                            'success': success,
                            'error': error,
                            'start_time': t0,
                            'end_time': t1,
                            'duration': (t1 - t0),
                            'rows_affected': rows_affected,
                            'rows_processed': rows_affected,
                            'error_code': None,
                            'memory_usage': 0,
                            'cpu_time': 0,
                        }]
                    elif db_type == 'redis':
                        command = query.get('command')
                        args = query.get('args', [])
                        t0 = time.time()
                        res = getattr(nonrel_client, command)(*args)
                        t1 = time.time()
                        results = [{
                            'success': True,
                            'start_time': t0,
                            'end_time': t1,
                            'duration': (t1 - t0),
                            'rows_affected': 0,
                            'rows_processed': 0
                        }]
                except Exception as e:
                    results = [{'success': False, 'error': str(e)}]
            else:
                results = executor.execute_batch([query])

            for i, result in enumerate(results):
                test_case_id = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))
                logical_thread = key
                thread_name_val = build_thread_name(logical_thread)
                # New query_id format: jobid_testcaseid_{thread_name}_{local_count}_{i_index}
                metric_id = f"{job_id}_{test_case_id}_{thread_name_val}_{local_count}_{i_index or i}"
                file_name = query.get('file_name', '') if isinstance(query, dict) else ''
                operation = query.get('operation', '') if isinstance(query, dict) else ''
                complexity = query.get('complexity', '') if isinstance(query, dict) else ''

                # Compose duration from available fields
                total_duration = result.get('total_duration')
                if total_duration is None:
                    if result.get('duration') is not None:
                        total_duration = result['duration']
                    elif result.get('start_time') is not None and result.get('end_time') is not None:
                        try:
                            total_duration = float(result['end_time']) - float(result['start_time'])
                        except Exception:
                            total_duration = 0.0
                    else:
                        total_duration = 0.0

                # Configurable retry logic
                if retry_enabled and (total_duration == 0 or total_duration is None):
                    if not (retry_skip_nonrelational and db_type in ['mongodb', 'redis']):
                        for attempt in range(retry_count):
                            try:
                                retry_results = executor.execute_batch([query])
                                if retry_results and isinstance(retry_results, list) and len(retry_results) > 0:
                                    retry = retry_results[0]
                                    retry_duration = retry.get('total_duration') or retry.get('duration')
                                    if retry_duration is None and retry.get('start_time') and retry.get('end_time'):
                                        try:
                                            retry_duration = float(retry.get('end_time')) - float(retry.get('start_time'))
                                        except Exception:
                                            retry_duration = None
                                    if retry_duration:
                                        total_duration = retry_duration
                                        # merge useful fields
                                        result.update(retry)
                                        break
                            except Exception:
                                continue

                # Compose thread_name with folder_base and logical thread info
                # Always use logical thread as key (e.g., read_simple, write_insert_simple)
                logical_thread = key
                thread_name_val = build_thread_name(logical_thread)
                # Set return_code: 0=success, 1=failure, 9=killed (if applicable)
                if result.get('success') is True:
                    return_code_val = 0
                elif result.get('success') is False:
                    return_code_val = 1
                elif result.get('error', '').lower() == 'killed':
                    return_code_val = 9
                else:
                    return_code_val = 1 if result.get('error') else 0
                metric_full = {
                    'job_id': job_id,
                    'test_case_id': test_case_id,
                    'query_id': metric_id,
                    'start_time': result.get('start_time'),
                    'end_time': result.get('end_time'),
                    'duration': total_duration,
                    'total_duration': total_duration,
                    'success': result.get('success'),
                    'error': result.get('error'),
                    'rows_affected': result.get('rows_affected', 0),
                    'memory_usage': result.get('memory_usage', 0),
                    'cpu_time': result.get('cpu_time', 0),
                    'query': query.get('query', '') if isinstance(query, dict) else str(query),
                    'file_name': file_name,
                    'operation': operation,
                    'complexity': complexity,
                    'thread_name': thread_name_val,
                    'return_code': return_code_val,
                    'error_code': result.get('error_code', ''),
                    'rows_processed': result.get('rows_affected', 0),
                    'user_id': user_id
                }
                metrics.record_query_metrics(metric_id, metric_full)
                if db_type in ['postgresql', 'mysql', 'mssql', 'oracle'] and db_conn:
                    insert_metric_to_db(metric_full, db_conn, user_id, db_type)
                if not result.get('success', True):
                    logger.error(f"[{job_id}][{test_case_id}][{user_id}][{key}][thread-{local_count}] Query error: {result.get('error')} | Query: {query.get('query', query)}")
                else:
                    logger.debug(f"[{job_id}][{test_case_id}][{user_id}][{key}][thread-{local_count}] Query success | Query: {query.get('query', query)}")

        # Different loop behaviours depending on single_run settings
        if duration == 0 and single_run_flag and single_run_mode == 'per_query_once':
            # Consume each queue item once, do not replenish
            while True:
                try:
                    query = q.get_nowait()
                except queue.Empty:
                    break
                process_query(query, local_count)
                local_count += 1
            return

        # Time-based or per-thread-count mode
        if duration == 0 and single_run_flag and single_run_mode == 'per_thread':
            runs_allowed = queries_per_connection
            run_counter = 0
            def should_continue():
                return run_counter < runs_allowed
        else:
            def should_continue():
                return time.time() - start_time < duration

        while should_continue():
            try:
                query = q.get(timeout=1)
            except queue.Empty:
                # Only replenish in continuous/time-based modes
                if not (duration == 0 and single_run_flag and single_run_mode == 'per_query_once'):
                    replenish_queues()
                continue
            process_query(query, local_count)
            local_count += 1
            # Increment run counter when running in per-thread mode
            try:
                if duration == 0 and single_run_flag and single_run_mode == 'per_thread':
                    run_counter += 1
            except Exception:
                pass
    # After soak test, generate CSV report for all query metrics
    def generate_csv_report_from_json(json_path, config, job_id, result_folder, csv_report_name=None):
        import csv
        import os
        db_host = config['database'].get('host', '')
        db_username = config['database'].get('username', '')
        if csv_report_name:
            csv_path = os.path.join(result_folder, csv_report_name)
        else:
            csv_path = os.path.join(result_folder, f"query_metrics_report_{config['user_id']}.csv")
        with open(json_path, 'r') as jf:
            data = json.load(jf)
        query_metrics = data.get('query_metrics', [])
        from datetime import datetime
        def fmt_time(val):
            try:
                return datetime.fromtimestamp(float(val)).isoformat(sep=' ', timespec='seconds')
            except Exception:
                return ''
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = [
                'job_id', 'db_host', 'db_username', 'start_time', 'end_time', 'elapsed_time', 'query_gist', 'query_id', 'test_case_id',
                'file_name', 'operation', 'complexity', 'thread_name', 'return_code', 'error_code', 'error_desc', 'rows_processed',
                'memory_usage', 'cpu_time', 'success'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for m in query_metrics:
                # Use fields directly from metrics
                test_case_id = m.get('test_case_id', '')
                thread_name = m.get('thread_name', '')
                operation = m.get('operation', '')
                complexity = m.get('complexity', '')
                file_name = m.get('file_name', '')
                writer.writerow({
                    'job_id': job_id,
                    'db_host': db_host,
                    'db_username': db_username,
                    'start_time': fmt_time(m.get('start_time', '')),
                    'end_time': fmt_time(m.get('end_time', '')),
                    'elapsed_time': m.get('duration', ''),
                    'query_gist': (m.get('query', '') or '')[:200],
                    'query_id': m['query_id'],
                    'test_case_id': test_case_id,
                    'file_name': file_name,
                    'operation': operation,
                    'complexity': complexity,
                    'thread_name': thread_name,
                    'return_code': m.get('return_code', ''),
                    'error_code': m.get('error_code', ''),
                    'error_desc': m.get('error', ''),
                    'rows_processed': m.get('rows_processed', ''),
                    'memory_usage': m.get('memory_usage', ''),
                    'cpu_time': m.get('cpu_time', ''),
                    'success': m.get('success', '')
                })

    # Launch threads
    threads = []
    for thread_info in thread_assignments:
        t = threading.Thread(target=thread_runner, args=(thread_info,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    logger.info(f"[{job_id}] Generating final performance report")
    report = metrics.get_performance_report(user_id)
    # Use raw normalized metrics for richer plots and reports (includes operation/complexity/file_name, etc.)
    MetricsUtils.generate_performance_plots(metrics.raw_query_metrics, os.path.join(result_folder, 'plots'))
    MetricsUtils.generate_metrics_report(metrics.raw_query_metrics, os.path.join(result_folder, html_report_name), db_config)
    metrics_json_path = os.path.join(result_folder, json_report_name)
    metrics.export_metrics(metrics_json_path)
    generate_csv_report_from_json(metrics_json_path, user_config, job_id, result_folder, csv_report_name)
    logger.info(f"[{job_id}] Soak test completed.")
    if handler:
        handler.close()

def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Database Soak Test Runner')
    parser.add_argument('--config', '-c', 
                      help='Path to the configuration file (e.g., configs/read_heavy_load.json)',
                      default='config.json')
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        print("\nAvailable configurations in configs/ directory:")
        configs_dir = 'configs'
        if os.path.exists(configs_dir):
            for file in os.listdir(configs_dir):
                if file.endswith('.json'):
                    print(f"  - {os.path.join(configs_dir, file)}")
        return

    settings = Settings(args.config)
    LoggingUtils.setup_logging(settings.get_logging_config())
    users = settings.config.get('users', [])
    logger = LoggingUtils.get_logger("main")
    
    if not users:
        logger.error(f"No users found in {args.config}")
        return

    logger.info(f"Starting soak tests for {len(users)} users")
    with ThreadPoolExecutor(max_workers=len(users)) as executor:
        futures = [executor.submit(run_user_soak, user) for user in users]
        for future in futures:
            future.result()

if __name__ == "__main__":
    main()