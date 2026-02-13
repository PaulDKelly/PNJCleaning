import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from backend directory
env_path = os.path.join(os.getcwd(), 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# Supabase Config
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment.")
    sys.exit(1)

supabase: Client = create_client(url, key)

def check_table(table_name):
    try:
        res = supabase.table(table_name).select("*", count="exact", head=True).execute()
        print(f"{table_name}: {res.count} rows")
    except Exception as e:
        print(f"{table_name}: Error - {e}")

def main():
    print("Verifying Supabase Cloud Data...")
    tables = [
        "brands", "users", "engineers", "clients", "client_sites", 
        "jobs", "extraction_reports", "extraction_micron_readings", 
        "extraction_inspection_items", "extraction_filter_items", 
        "extraction_photos"
    ]
    for table in tables:
        check_table(table)

if __name__ == "__main__":
    main()
