-- Schema for soak_test_metrics table
-- This table stores performance metrics from database soak tests
-- Compatible with PostgreSQL, MySQL, MSSQL, and Oracle (with minor adjustments)

-- PostgreSQL / MySQL
CREATE TABLE IF NOT EXISTS soak_test_metrics (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(24) NOT NULL,
    test_case_id VARCHAR(24) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration DECIMAL(20, 6) NOT NULL,
    success BOOLEAN NOT NULL,
    error TEXT,
    rows_affected INTEGER DEFAULT 0,
    memory_usage DECIMAL(10, 2) DEFAULT 0,
    cpu_time DECIMAL(10, 2) DEFAULT 0,
    query_gist VARCHAR(200),
    file_name VARCHAR(255),
    operation VARCHAR(50),
    complexity VARCHAR(50),
    thread_name VARCHAR(100),
    return_code VARCHAR(10),
    error_code VARCHAR(50),
    error_desc TEXT,
    rows_processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_job_id ON soak_test_metrics(job_id);
CREATE INDEX IF NOT EXISTS idx_test_case_id ON soak_test_metrics(test_case_id);
CREATE INDEX IF NOT EXISTS idx_start_time ON soak_test_metrics(start_time);
CREATE INDEX IF NOT EXISTS idx_success ON soak_test_metrics(success);
CREATE INDEX IF NOT EXISTS idx_operation ON soak_test_metrics(operation);
CREATE INDEX IF NOT EXISTS idx_complexity ON soak_test_metrics(complexity);
CREATE INDEX IF NOT EXISTS idx_thread_name ON soak_test_metrics(thread_name);

-- For MSSQL, replace SERIAL with:
-- id INT IDENTITY(1,1) PRIMARY KEY,
-- and BOOLEAN with BIT
-- and TEXT with VARCHAR(MAX)
-- and IF NOT EXISTS with appropriate syntax

-- For Oracle, replace SERIAL with:
-- id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
-- and BOOLEAN with NUMBER(1) (0 or 1)
-- and TEXT with CLOB
-- and remove IF NOT EXISTS (or use BEGIN/EXCEPTION block)
