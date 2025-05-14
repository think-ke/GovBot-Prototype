"""
Simple wrapper script to run the indexing columns migration.
This provides a more user-friendly way to run the required database migration.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration script to add indexing columns to the database."""
    try:
        # Get the path to the migration script
        script_dir = Path(__file__).parent
        migration_script = script_dir / "add_indexing_columns.py"
        
        # Check if the migration script exists
        if not migration_script.exists():
            logger.error(f"Migration script not found: {migration_script}")
            print(f"Error: Migration script not found: {migration_script}")
            return False
        
        print("Running database migration to add indexing columns...")
        
        # Set environment variables for the subprocess
        env = os.environ.copy()
        
        # Set DATABASE_URL if not already set
        if "DATABASE_URL" not in env:
            env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/govstackdb"
        elif "localhost" in env["DATABASE_URL"] and os.name == "nt":
            # Replace localhost with 127.0.0.1 on Windows to avoid DNS resolution issues
            env["DATABASE_URL"] = env["DATABASE_URL"].replace("localhost", "127.0.0.1")
        
        # Run the migration script with the environment variables
        result = subprocess.run(
            [sys.executable, str(migration_script)],
            capture_output=True,
            text=True,
            check=False,
            env=env
        )
        
        # Check the result
        if result.returncode == 0:
            print("\nSuccess! Database migration completed.")
            print("\nThe following columns have been added to the webpages table:")
            print("  - is_indexed (Boolean): Tracks whether a webpage has been indexed")
            print("  - indexed_at (Timestamp): Records when a webpage was indexed")
            print("\nYou can now use the collection stats endpoint and indexing features.")
            return True
        else:
            print("\nError: Migration failed.")
            print(f"Error output: {result.stderr}")
            print("\nYou may need to check your database connection or permissions.")
            
            # Show additional debugging info for common issues
            if "connection refused" in result.stderr.lower():
                print("\nTip: Make sure your PostgreSQL server is running and accessible.")
            elif "asyncpg.exceptions" in result.stderr:
                print("\nTip: This appears to be a database driver issue. Try installing asyncpg:")
                print("     pip install asyncpg")
            
            return False
            
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        print(f"\nAn unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    run_migration()
