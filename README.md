# Database Soak Testing Framework

A comprehensive, extensible framework for conducting database soak tests with advanced performance metrics collection, analysis, and visualization.

## Features

### Core Capabilities
- **Multi-database support**: PostgreSQL, MySQL, MSSQL, Oracle, MongoDB, Redis
- **Multi-user concurrent testing**: Run multiple test scenarios simultaneously with isolated configs
- **Extensible architecture**: Plugin-based system for database handlers, reporters, and hooks
- **Intelligent query management**: 
  - Hierarchical query organization (operation → complexity → queries)
  - Queue-based query distribution with automatic replenishment
  - Thread assignment strategies (fixed count or weighted distribution)
- **Flexible execution modes**:
  - Time-based soak testing
  - Fixed iteration per thread
  - Single execution per query file
- **Configurable retry logic**: Smart retry with duration-based triggers and DB-type filtering

### Metrics & Reporting
- **Comprehensive metrics collection**:
  - Query execution times (total, p50, p90, p95, p99)
  - Success rates and error categorization
  - Operation and complexity-based analysis
  - Thread-level performance tracking
- **Rich visualizations**:
  - Duration distribution by operation and complexity
  - Success rate timelines
  - Box plots for performance comparison
  - All plots use consistent color schemes and legends
- **Multiple report formats**:
  - HTML reports with embedded plots and detailed tables
  - CSV exports with full metric details
  - JSON exports for programmatic access
  - Random sampling of 50 queries for quick review

### Advanced Features
- Configurable thread ratios for read/write and complexity distribution
- Dynamic queue replenishment for continuous load
- Unique job IDs for isolated test runs
- Structured logging with per-job log files
- Database metrics insertion (PostgreSQL, MySQL, MSSQL, Oracle)
- Hook system for pre/post query and test event handling

## Installation

### Prerequisites
- Python 3.9 or higher
- Target database(s) running and accessible
- For MongoDB: Running MongoDB instance
- For Redis: Running Redis instance

### Quick Start

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/database-soak-test.git
cd database-soak-test
```

2. **Create and activate virtual environment**:
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/Mac:
source .venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Required Packages
Core dependencies are organized in `requirements.txt`:
- **Database drivers**: sqlalchemy (2.0+), psycopg2-binary, pymysql, pyodbc, oracledb
- **NoSQL clients**: pymongo, redis
- **Data processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn (static plots only)
- **Logging**: loguru
- **Testing**: pytest, pytest-cov

### Database-Specific Setup

#### Oracle Database
For Oracle support, the framework uses the `oracledb` driver (formerly known as cx_Oracle). 

**Installation**:
```bash
pip install oracledb
```

**Connection Configuration**:
Oracle connections require the following parameters in your config file:
```json
{
  "database": {
    "db_type": "oracle",
    "host": "localhost",
    "port": 1521,
    "database": "ORCLPDB1",
    "service_name": "ORCLPDB1",
    "username": "system",
    "password": "oracle"
  }
}
```

**Key points**:
- Use `service_name` for Oracle service name (defaults to `database` value if not specified)
- Default Oracle port is 1521
- Ensure the Oracle client libraries are installed if using thick mode
- For Oracle Autonomous Database, download the wallet and configure TNS_ADMIN

**Example configuration**: See `configs/oracle_example.json`

**Example queries**: See `queries/oracle/README.md` for Oracle-specific query examples and setup instructions

## Configuration

### Configuration Structure

The framework uses JSON configuration files supporting multi-user scenarios. Pre-configured templates are available in `configs/`:
- `read_heavy_load.json` - 80% read, 20% write operations
- `write_heavy_load.json` - 30% read, 70% write operations  
- `mixed_load.json` - 50/50 read/write balance
- `quick_read_smoke.json` - Short smoke test (10 seconds)

### Configuration Options

```json
{
  "users": [
    {
      "user_id": "unique_user_identifier",
      "database": {
        "db_type": "postgresql",  // postgresql, mysql, mssql, oracle, mongodb, redis
        "host": "localhost",
        "port": 5432,
        "database": "your_database",
        "username": "your_username",
        "password": "your_password"
      },
      "test_config": {
        "concurrent_connections": 20,        // Number of concurrent threads
        "execution_time": 600,              // Duration in seconds (0 = single run mode)
        "queries_per_connection": 100,      // Queries per thread in per_thread mode
        "ramp_up_time": 30,                // Gradual thread startup (seconds)
        "metrics_interval": 60,             // Metrics collection frequency
        "single_run_mode": "per_thread",   // "per_thread" or "per_query_once"
        "retry": {
          "enabled": true,                  // Enable retry for failed queries
          "retries": 3,                     // Number of retry attempts
          "skip_nonrelational": true        // Skip retries for MongoDB/Redis
        }
      },
      "thread_ratios": {
        "read": 0.8,                        // 80% threads for read operations
        "write": 0.2,                       // 20% threads for write operations
        "read_complexity": {                // Read thread distribution
          "simple": 0.6,
          "medium": 0.3,
          "complex": 0.1
        },
        "write_operations": {               // Write operation distribution
          "insert": 0.4,
          "update": 0.4,
          "delete": 0.2
        },
        "write_complexity": {               // Write complexity distribution
          "simple": 0.7,
          "medium": 0.2,
          "complex": 0.1
        }
      },
      "queue_settings": {
        "replenish_interval": 5,            // Queue refill frequency (seconds)
        "max_queue_size": 2000              // Maximum queue capacity
      },
      "query_folder": "queries/postgresql"  // Path to query files
    }
  ],
  "logging": {
    "level": "INFO",                        // DEBUG, INFO, WARNING, ERROR
    "file": "logs/soak_test.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### Metrics Database Configuration (Optional)

You can optionally store test metrics in a separate database by creating a metrics database configuration file and passing it using the `--metrics-config` parameter. This allows you to:
- Keep metrics separate from your test target database
- Use a different database type or server for metrics storage
- Centralize metrics collection from multiple test runs

Create a metrics configuration file (e.g., `configs/metrics_db.json`):

```json
{
    "metrics_database": {
        "db_type": "postgresql",
        "host": "metrics-server.example.com",
        "port": 5432,
        "database": "metrics_db",
        "username": "metrics_user",
        "password": "metrics_password",
        "table_name": "soak_test_metrics"
    }
}
```

**Supported Metrics Database Types**: PostgreSQL, MySQL, MSSQL, Oracle

**Using the Metrics Configuration**:
```bash
# Run tests with separate metrics database
python main.py -c configs/read_heavy_load.json -m configs/metrics_db.json

# Short form
python main.py -c configs/read_heavy_load.json --metrics-config configs/metrics_db.json
```

**Note**: If no metrics configuration is provided, metrics will be stored in the test target database (default behavior).

**Setting up the Metrics Table**:

Before running tests with a separate metrics database, ensure the `soak_test_metrics` table exists. Use the provided schema:

```bash
# For PostgreSQL
psql -h metrics-server.example.com -U metrics_user -d metrics_db -f configs/metrics_table_schema.sql

# For MySQL
mysql -h metrics-server.example.com -u metrics_user -p metrics_db < configs/metrics_table_schema.sql
```

The schema file (`configs/metrics_table_schema.sql`) includes:
- Table structure with all required columns
- Indexes for optimal query performance
- Notes for adapting to MSSQL and Oracle

### Query File Organization

Queries must be organized in a hierarchical structure:
```
queries/
├── postgresql/
│   ├── read/
│   │   └── select/
│   │       ├── simple/
│   │       │   └── query1.sql
│   │       ├── medium/
│   │       │   └── query1.sql
│   │       └── complex/
│   │           └── query1.sql
│   └── write/
│       ├── insert/
│       │   └── simple/
│       │       └── query1.sql
│       ├── update/
│       │   └── simple/
│       │       └── query1.sql
│       └── delete/
│           └── simple/
│               └── query1.sql
```

## Usage

### Running a Soak Test

#### Basic Usage
```bash
# Run with default config
python main.py

# Run with specific config
python main.py -c configs/read_heavy_load.json

# Quick smoke test (10 seconds)
python main.py -c configs/quick_read_smoke.json

# Run with separate metrics database
python main.py -c configs/read_heavy_load.json -m configs/metrics_db.json
```

#### With Virtual Environment
```bash
# Windows PowerShell
& ".venv\Scripts\python.exe" main.py -c configs/read_heavy_load.json

# Linux/Mac
.venv/bin/python main.py -c configs/read_heavy_load.json
```

### Understanding Test Execution

1. **Job ID Generation**: Each test run creates a unique 24-character job ID
2. **Isolated Reports**: Results are stored in `reports/<db_type>_<test_type>_<db_user>_<job_id>_<timestamp>/`
3. **Thread Distribution**: Threads are assigned based on configured ratios
4. **Query Loading**: Queries are loaded from structured folders into queues
5. **Execution Modes**:
   - **Time-based**: Runs for specified duration
   - **Per-thread**: Each thread executes N queries
   - **Per-query-once**: Each query file executed once across all threads

### Report Outputs

Each test run generates multiple output files under a uniquely named folder:
`reports/<db_type>_<test_type>_<db_user>_<job_id>_<timestamp>/`

#### 1. HTML Report (`test_report_<test_type>_<db_user>_<job_id>.html`)
- **Summary Statistics**: Total queries, success rates, duration percentiles
- **Breakdown Tables**: 
  - Overall statistics
  - Read vs Write operations comparison
  - Performance by complexity level
- Title reflects test type: "Database Load Test Metrics Report" or "Database Soak Test Metrics Report"
- **Static Plots** (PNG):
  - Duration distribution by operation
  - Duration distribution by complexity
  - Success rate timeline
- **Sample Metrics**: Random 50 queries with full details

#### 2. CSV Export (`query_metrics_report_<test_type>_<db_user>_<job_id>.csv`)
Complete query-level data including:
- Job ID, test case ID, timestamps
- Query details (file, operation, complexity)
- Performance metrics (duration, success, rows)
- Thread information
- Error details (if any)

#### 3. JSON Metrics (`metrics_<test_type>_<db_user>_<job_id>.json`)
Raw metrics data for programmatic access:
- All query executions with full metadata
- Connection-level aggregations
- Suitable for custom analysis or dashboards

#### 4. Plots Directory (`plots/`)
Static PNG visualizations:
- `duration_distribution_by_operation.png`
- `duration_by_complexity.png`
- `success_rate_timeline.png`

#### 5. Logs (`logs/<db_type>_<test_type>_<db_user>_<job_id>_<timestamp>.log`)
Detailed execution logs with:
- Thread assignments
- Query execution traces
- Error details and stack traces
- Performance report generation steps

### Programmatic Usage

### Conventions and Formats

#### Test Type Mapping
- `single_run_mode: "per_thread"` → `test_type: "soaktest"`
- `single_run_mode: "per_query_once"` → `test_type: "loadtest"`

#### Thread Naming
- Every metric includes `thread_name` in the format: `{test_type}_{suffix}`
  - Read threads: suffix is the complexity (`simple`, `medium`, `complex`) → e.g., `loadtest_simple`, `soaktest_complex`
  - Write threads: suffix is `operation_complexity` → e.g., `loadtest_insert_simple`, `soaktest_update_medium`

#### Query ID Format
- `query_id = {job_id}_{test_case_id}_{thread_name}_{local_count}_{i_index}`
- Always includes the exact `thread_name`; no user_id or config/test prefixes inside `query_id`.

#### Return Codes
- `return_code` values:
  - `0` → success
  - `1` → failure
  - `9` → killed

For custom integrations or automation:

```python
from src.config.settings import Settings
from src.utils.logging_utils import LoggingUtils
from src.utils.metrics_utils import MetricsUtils
from src.core.performance_metrics import PerformanceMetrics

# Load configuration
settings = Settings('configs/read_heavy_load.json')
LoggingUtils.setup_logging(settings.get_logging_config())

# Access individual user configs
users = settings.config.get('users', [])
for user_config in users:
    # Run custom test logic
    pass

# Generate custom reports
metrics = PerformanceMetrics()
# ... collect metrics ...
MetricsUtils.generate_performance_plots(
    metrics.raw_query_metrics, 
    'custom_output/plots'
)
MetricsUtils.generate_metrics_report(
    metrics.raw_query_metrics,
    'custom_output/report.html'
)
```

## Architecture

### Core Components

#### 1. Database Handler Registry (`src/core/db_handler.py`)
Pluggable system for different database types:
- Abstraction layer for relational and non-relational databases
- Factory pattern for handler instantiation
- Support for PostgreSQL, MySQL, MSSQL, Oracle, MongoDB, Redis

#### 2. Executor Abstraction (`src/core/executor.py`, `src/core/sqlalchemy_executor.py`)
- Base executor interface for query execution
- SQLAlchemy-based executor for relational databases
- Timing and error capture
- Batch execution support

#### 3. Performance Metrics (`src/core/performance_metrics.py`)
- Dual metric storage (dataclass + raw dict)
- Automatic field normalization and enrichment
- Connection-level aggregations
- Export to JSON with ISO8601 timestamps

#### 4. Queue Manager (`src/queue/queue_manager.py`)
- Hierarchical query discovery
- Per-operation/complexity queue management
- Automatic replenishment
- Fallback query generation

#### 5. Thread Strategies (`src/threads/thread_strategy.py`)
- FixedCountStrategy: Equal thread distribution
- WeightedStrategy: Ratio-based allocation
- Extensible strategy pattern

#### 6. Reporter Plugins (`src/reporting/`)
- CSV, DB, and base reporter implementations
- Extensible reporter interface
- Buffered database insertion

#### 7. Hook System (`src/plugins/hooks.py`)
Pre/post execution hooks for:
- Query-level events (before/after execution)
- Test-level events (setup/teardown)
- Safe error handling
- Example hooks provided

### Extensibility

#### Adding a New Database Type
```python
# 1. Create handler in src/core/db_handler.py
class NewDBHandler:
    def connect(self, conn_id, config):
        # Connection logic
        pass
    
    def get_executor(self, conn_id):
        return CustomExecutor(self.connection)
    
    def close(self):
        # Cleanup
        pass

# 2. Register in get_db_handler()
if db_type == 'newdb':
    return NewDBHandler()
```

#### Adding Custom Metrics
```python
# Extend QueryMetrics dataclass
@dataclass
class CustomQueryMetrics(QueryMetrics):
    custom_field: str = ''
    custom_metric: float = 0.0
```

#### Adding Custom Reporters
```python
from src.reporting.reporter import Reporter

class CustomReporter(Reporter):
    def report(self, metrics: List[Dict]):
        # Custom reporting logic
        pass
```

## Troubleshooting

### Common Issues

1. **SQLAlchemy ImportError**: Ensure SQLAlchemy 2.0+ is installed
   ```bash
   pip install --upgrade sqlalchemy
   ```

2. **Missing Queries**: Check query folder structure matches expected hierarchy

3. **Connection Errors**: Verify database credentials and network connectivity

4. **Plot Generation Fails**: Ensure matplotlib backend is set to 'Agg' for headless systems

5. **Large Output Files**: For long-running tests, consider:
   - Reducing `metrics_interval`
   - Using sampling in reports
   - Implementing log rotation

### Debug Mode
Enable detailed logging:
```json
{
  "logging": {
    "level": "DEBUG",
    "file": "logs/debug.log"
  }
}
```

## Performance Tips

1. **Queue Sizing**: Balance `max_queue_size` with memory constraints
2. **Replenish Interval**: Lower values increase overhead but ensure queue availability
3. **Thread Count**: Optimal count depends on database capacity and query complexity
4. **Batch Size**: Larger batches reduce overhead but increase memory usage
5. **Metrics Interval**: Higher intervals reduce I/O overhead

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow existing code style and patterns
4. Add tests for new functionality
5. Update documentation (README, docstrings)
6. Commit with clear messages (`git commit -m 'Add: feature description'`)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Open a Pull Request with detailed description

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest src/tests/

# Check code style
black --check .
flake8 src/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Recent Improvements
- ✅ Removed interactive plots (plotly dependency eliminated)
- ✅ Enhanced static plot legends and color consistency
- ✅ Added read/write operation breakdown in HTML reports
- ✅ Random sampling of 50 queries in reports
- ✅ Fixed user_id display in sample metrics
- ✅ Separate plots for operation and complexity distributions
- ✅ Improved metric value filling and formatting
- ✅ SQLAlchemy 2.0 compatibility
- ✅ Extensible architecture with registry pattern
- ✅ Configurable retry logic with smart triggers