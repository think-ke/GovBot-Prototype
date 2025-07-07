-- Create Metabase database
-- This script runs during PostgreSQL container initialization

-- Create the metabase database for Metabase application data
SELECT 'CREATE DATABASE metabase'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'metabase')\gexec
