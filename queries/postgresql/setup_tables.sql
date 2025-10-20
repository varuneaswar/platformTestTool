-- Table for soak test queries
CREATE TABLE IF NOT EXISTS soak_test_data (
    id SERIAL PRIMARY KEY,
    test_case_id VARCHAR(24) NOT NULL,
    query_text TEXT NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    error TEXT
);

-- Table for metrics collection
CREATE TABLE IF NOT EXISTS soak_test_metrics (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(24) NOT NULL,
    test_case_id VARCHAR(24) NOT NULL,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration FLOAT,
    success BOOLEAN,
    error TEXT,
    rows_affected INT,
    memory_usage FLOAT,
    cpu_time FLOAT
);
