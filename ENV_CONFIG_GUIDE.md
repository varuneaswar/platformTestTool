# Environment-Based Database Configuration Guide

This guide explains how to use the new environment-based database configuration features in the platform test tool.

## Overview

The platform test tool now supports:
- ✅ **Secure credential management** via environment variables
- ✅ **Multiple database configurations** in a single setup
- ✅ **Backwards compatibility** with existing config files
- ✅ **Flexible configuration** mixing files and environment variables

## Quick Start

### 1. Set Up Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:
```bash
# PostgreSQL Primary Database
DB_POSTGRES_PRIMARY_TYPE=postgresql
DB_POSTGRES_PRIMARY_HOST=localhost
DB_POSTGRES_PRIMARY_PORT=5432
DB_POSTGRES_PRIMARY_NAME=postgres
DB_POSTGRES_PRIMARY_USER=postgres
DB_POSTGRES_PRIMARY_PASSWORD=your_actual_password
```

**Important**: The `.env` file is automatically excluded from version control to prevent credential leaks.

### 2. Create Configuration File

#### Option A: Environment-Based (Recommended)
```json
{
  "users": [
    {
      "user_id": "user1",
      "database_ref": "postgres_primary",
      "test_config": { ... },
      "thread_ratios": { ... },
      "query_folder": "queries/postgresql"
    }
  ],
  "logging": { ... }
}
```

#### Option B: Centralized Databases
```json
{
  "databases": {
    "postgres_primary": {
      "db_type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database": "postgres",
      "username": "postgres",
      "password": "admin"
    },
    "mysql_primary": {
      "db_type": "mysql",
      "host": "localhost",
      "port": 3306,
      "database": "testdb",
      "username": "root",
      "password": "admin"
    }
  },
  "users": [
    {
      "user_id": "user1_postgres",
      "database_ref": "postgres_primary",
      ...
    },
    {
      "user_id": "user2_mysql",
      "database_ref": "mysql_primary",
      ...
    }
  ]
}
```

### 3. Run Tests

```bash
python main.py -c configs/env_based_example.json
```

## Configuration Patterns

### Pattern 1: Secure Credentials (Best Practice)

**Scenario**: Keep credentials out of version control

**.env file**:
```bash
DB_PRODUCTION_TYPE=postgresql
DB_PRODUCTION_HOST=prod-db.example.com
DB_PRODUCTION_PORT=5432
DB_PRODUCTION_NAME=production
DB_PRODUCTION_USER=prod_user
DB_PRODUCTION_PASSWORD=super_secret_password
```

**config.json**:
```json
{
  "users": [{
    "user_id": "prod_test",
    "database_ref": "production",
    ...
  }]
}
```

### Pattern 2: Multiple Databases

**Scenario**: Test against multiple database instances simultaneously

**config.json**:
```json
{
  "databases": {
    "postgres_primary": { ... },
    "postgres_replica": { ... },
    "mysql_primary": { ... }
  },
  "users": [
    {"user_id": "test_pg_primary", "database_ref": "postgres_primary"},
    {"user_id": "test_pg_replica", "database_ref": "postgres_replica"},
    {"user_id": "test_mysql", "database_ref": "mysql_primary"}
  ]
}
```

### Pattern 3: Environment Overrides

**Scenario**: Different credentials per environment (dev/staging/prod)

**config.json** (checked into git):
```json
{
  "databases": {
    "app_database": {
      "db_type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database": "appdb",
      "username": "appuser",
      "password": "default_password"
    }
  }
}
```

**.env.dev** (local development):
```bash
DB_APP_DATABASE_HOST=localhost
DB_APP_DATABASE_PASSWORD=dev_password
```

**.env.prod** (production server):
```bash
DB_APP_DATABASE_HOST=prod-db.example.com
DB_APP_DATABASE_PASSWORD=production_password
```

### Pattern 4: Backwards Compatible

**Scenario**: Migrate gradually from old config format

**Old format still works**:
```json
{
  "users": [{
    "user_id": "user1",
    "database": {
      "db_type": "postgresql",
      "host": "localhost",
      "port": 5432,
      "database": "postgres",
      "username": "postgres",
      "password": "admin"
    },
    ...
  }]
}
```

**Can be enhanced with environment variables**:
```bash
# Override password for security
DB_USER1_PASSWORD=secure_password
```

## Environment Variable Naming Convention

The naming convention follows this pattern:
```
DB_{CONNECTION_ID}_{PARAMETER}
```

Where:
- `CONNECTION_ID`: The database reference name (uppercase)
- `PARAMETER`: The configuration parameter (uppercase)

### Examples:

| Config Value | Environment Variable |
|--------------|---------------------|
| db_type | DB_POSTGRES_PRIMARY_TYPE |
| host | DB_POSTGRES_PRIMARY_HOST |
| port | DB_POSTGRES_PRIMARY_PORT |
| database | DB_POSTGRES_PRIMARY_NAME |
| username | DB_POSTGRES_PRIMARY_USER |
| password | DB_POSTGRES_PRIMARY_PASSWORD |
| service_name | DB_ORACLE_PRIMARY_SERVICE_NAME |

### For Inline Configs:

When using inline database configs (without `database_ref`), use the `user_id`:
```bash
DB_USER1_HOST=localhost
DB_USER1_PASSWORD=secret
```

## Security Best Practices

1. **Never commit .env files**
   - The `.env` file is in `.gitignore`
   - Use `.env.example` as a template

2. **Use environment variables for sensitive data**
   - Store passwords in `.env` files
   - Keep non-sensitive config in JSON files

3. **Different credentials per environment**
   - Use `.env.dev`, `.env.staging`, `.env.prod`
   - Load appropriate file per environment

4. **Rotate credentials regularly**
   - Update `.env` file
   - No code changes needed

5. **Limit credential access**
   - Restrict who can access `.env` files
   - Use secret management tools in production

## Migration Guide

### From Old Format to New Format

**Before** (config.json):
```json
{
  "users": [{
    "user_id": "user1",
    "database": {
      "db_type": "postgresql",
      "host": "localhost",
      "password": "admin"
    }
  }]
}
```

**After** (config.json + .env):

**config.json**:
```json
{
  "users": [{
    "user_id": "user1",
    "database_ref": "postgres_primary"
  }]
}
```

**.env**:
```bash
DB_POSTGRES_PRIMARY_TYPE=postgresql
DB_POSTGRES_PRIMARY_HOST=localhost
DB_POSTGRES_PRIMARY_PASSWORD=admin
```

## Troubleshooting

### Issue: "No configuration found for connection"

**Cause**: Database reference not found in config or environment

**Solution**: 
- Check that `database_ref` matches a key in the `databases` section
- Or ensure environment variables are set for that connection ID

### Issue: Environment variables not loading

**Cause**: `.env` file not in the correct location

**Solution**:
- Place `.env` file in the project root directory
- Ensure the file is named exactly `.env` (no extra extensions)

### Issue: Credentials still in config file

**Cause**: Using old inline format

**Solution**:
- Move to `database_ref` pattern
- Define databases in centralized `databases` section or `.env` file

## Examples

See the following example files:
- `configs/env_based_example.json` - Environment variable based
- `configs/multi_database_example.json` - Multiple databases
- `.env.example` - Template for environment variables

## Support

For questions or issues, please refer to:
- README.md - Full documentation
- .env.example - Configuration template
- Example config files in `configs/` directory
