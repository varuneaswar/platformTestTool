#!/usr/bin/env python3
"""
Simple validation script to test metrics database configuration loading.
This does not require a running database - it only validates that the 
configuration files are properly structured and can be loaded.
"""

import json
import sys
import os

def validate_metrics_config(config_path):
    """Validate a metrics database configuration file."""
    print(f"Validating metrics config: {config_path}")
    
    if not os.path.exists(config_path):
        print(f"  ❌ File not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for metrics_database key
        if 'metrics_database' not in config:
            print("  ❌ Missing 'metrics_database' key")
            return False
        
        metrics_db = config['metrics_database']
        
        # Check required fields
        required_fields = ['db_type', 'host', 'port', 'database', 'username', 'password']
        missing = [f for f in required_fields if f not in metrics_db]
        if missing:
            print(f"  ❌ Missing required fields: {missing}")
            return False
        
        # Check supported database types
        supported_types = ['postgresql', 'mysql', 'mssql', 'oracle']
        db_type = metrics_db['db_type'].lower()
        if db_type not in supported_types:
            print(f"  ⚠️  Unsupported db_type '{db_type}'. Supported: {supported_types}")
            print(f"     Metrics will not be stored to database.")
        
        # Check table_name (optional, has default)
        table_name = metrics_db.get('table_name', 'soak_test_metrics')
        
        print(f"  ✓ Valid configuration")
        print(f"    - Database Type: {metrics_db['db_type']}")
        print(f"    - Host: {metrics_db['host']}:{metrics_db['port']}")
        print(f"    - Database: {metrics_db['database']}")
        print(f"    - Username: {metrics_db['username']}")
        print(f"    - Table: {table_name}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def validate_test_config(config_path):
    """Validate a test configuration file."""
    print(f"\nValidating test config: {config_path}")
    
    if not os.path.exists(config_path):
        print(f"  ❌ File not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check for users key
        if 'users' not in config:
            print("  ❌ Missing 'users' key")
            return False
        
        users = config['users']
        if not users:
            print("  ❌ No users configured")
            return False
        
        print(f"  ✓ Valid configuration with {len(users)} user(s)")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"  ❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run validation on configuration files."""
    print("=" * 60)
    print("Metrics Database Configuration Validator")
    print("=" * 60)
    
    # Test metrics configs
    metrics_configs = [
        'configs/metrics_db.json',
        'configs/metrics_db_mysql.json'
    ]
    
    metrics_valid = []
    for config in metrics_configs:
        if os.path.exists(config):
            valid = validate_metrics_config(config)
            metrics_valid.append((config, valid))
    
    # Test a sample test config
    test_configs = [
        'config.json',
        'configs/read_heavy_load.json'
    ]
    
    test_valid = []
    for config in test_configs:
        if os.path.exists(config):
            valid = validate_test_config(config)
            test_valid.append((config, valid))
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    print("\nMetrics Configurations:")
    for config, valid in metrics_valid:
        status = "✓ PASS" if valid else "✗ FAIL"
        print(f"  {status}: {config}")
    
    print("\nTest Configurations:")
    for config, valid in test_valid:
        status = "✓ PASS" if valid else "✗ FAIL"
        print(f"  {status}: {config}")
    
    all_valid = all(v for _, v in metrics_valid + test_valid)
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✓ All configurations are valid!")
        return 0
    else:
        print("✗ Some configurations have errors")
        return 1

if __name__ == '__main__':
    sys.exit(main())
