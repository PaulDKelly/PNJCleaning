import sqlite3
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

sqlite_path = 'e:/Code/Projects/PNJCleaning/backend/production.sqlite'

def migrate_table(sqlite_conn, table_name, supabase_table):
    print(f"Migrating {table_name}...")
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        record = dict(zip(columns, row))
        # Handle potential data type mismatches or default values if needed
        data.append(record)
    
    if data:
        try:
            # Using upsert to handle existing records
            res = supabase.table(supabase_table).upsert(data).execute()
            print(f"Successfully migrated {len(data)} records to {supabase_table}")
        except Exception as e:
            print(f"Error migrating {table_name}: {str(e)}")
    else:
        print(f"No records found in {table_name}")

def main():
    if not os.path.exists(sqlite_path):
        print(f"Error: {sqlite_path} not found.")
        return

    conn = sqlite3.connect(sqlite_path)
    
    # List of tables to migrate (source_table, destination_table)
    tables = [
        ("brands", "brands"),
        ("clients", "clients"),
        ("engineers", "engineers"),
        ("site_contacts", "site_contacts"),
        ("client_sites", "client_sites")
    ]
    
    for sqlite_table, supabase_table in tables:
        migrate_table(conn, sqlite_table, supabase_table)
        
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    main()
