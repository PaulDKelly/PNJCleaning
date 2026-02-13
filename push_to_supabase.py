import sqlite3
import os
import sys
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Add backend to path to import models if needed, though we can just use dicts for Supabase
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load environment variables from backend directory
env_path = os.path.join(os.getcwd(), 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to current dir if root env exists
    load_dotenv()

# Supabase Config
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    print(f"Error: SUPABASE_URL or SUPABASE_KEY not found in environment (checked {env_path}).")
    sys.exit(1)

supabase: Client = create_client(url, key)

# SQLite Config
sqlite_db = 'backend/pnj_database.db'
if not os.path.exists(sqlite_db):
    print(f"Error: SQLite database not found at {sqlite_db}")
    sys.exit(1)

def get_sqlite_data(table_name):
    conn = sqlite3.connect(sqlite_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def migrate_table(sqlite_table, supabase_table):
    print(f"Migrating {sqlite_table} -> {supabase_table}...")
    
    # 1. Get local data
    try:
        data = get_sqlite_data(sqlite_table)
    except sqlite3.OperationalError as e:
        print(f"  Warning: Table {sqlite_table} not found in SQLite ({e}). Skipping.")
        return

    if not data:
        print(f"  No data found in {sqlite_table}. Skipping.")
        return

    # 2. Clean and Insert
    print(f"  Found {len(data)} rows. Processing...")
    
    cleaned_data = []
    for row in data:
        clean_row = {}
        for k, v in row.items():
            # Handle timestamps and special types
            if isinstance(v, (datetime,)):
                clean_row[k] = v.isoformat()
            # Convert 'password' to 'password' if it exists, ensure nothing is lost
            clean_row[k] = v
        cleaned_data.append(clean_row)

    # Batch insert
    batch_size = 50
    for i in range(0, len(cleaned_data), batch_size):
        batch = cleaned_data[i:i + batch_size]
        try:
            # Upsert will overwrite if ID matches, or insert if new
            # We preserve IDs to maintain Foreign Key relationships
            res = supabase.table(supabase_table).upsert(batch).execute()
            print(f"  Batch {i//batch_size + 1}: Success ({len(batch)} rows)")
        except Exception as e:
            print(f"  Batch {i//batch_size + 1}: Error - {e}")

def main():
    print("Starting Migration from SQLite to Supabase...")
    
    # Order matters for Foreign Keys (Parent tables first)
    # Check both 'job' and 'job_schedule' as possible source table names
    tables_map = [
        ("brand", "brands"),
        ("user", "users"),
        ("engineer", "engineers"),
        ("client", "clients"),
        ("client_site", "client_sites"),
        ("site_contact", "site_contacts"),
        ("job", "jobs"),
        ("job_schedule", "jobs"), # Alternate name
        ("leave_request", "leave_requests"),
        ("extraction_report", "extraction_reports"),
        ("extraction_micron_reading", "extraction_micron_readings"),
        ("extraction_inspection_item", "extraction_inspection_items"),
        ("extraction_filter_item", "extraction_filter_items"),
        ("extraction_photo", "extraction_photos"),
        ("system_setting", "system_settings")
    ]
    
    for sqlite_t, supabase_t in tables_map:
        migrate_table(sqlite_t, supabase_t)

    print("\nMigration process completed!")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
