#!/bin/bash
set -e

echo "Creating metabase database..."

# Create the metabase database if it doesn't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE metabase' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase')\gexec
    GRANT ALL PRIVILEGES ON DATABASE metabase TO $POSTGRES_USER;
EOSQL

echo "Metabase database created successfully."
