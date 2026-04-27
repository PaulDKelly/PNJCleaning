from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

def check_table(table_name):
    try:
        res = supabase.table(table_name).select("*", count="exact").execute()
        count = res.count if hasattr(res, 'count') else len(res.data)
        print(f"Table '{table_name}': {count} rows")
        if res.data:
            print(f"Columns: {list(res.data[0].keys())}")
        else:
            print("No data.")
    except Exception as e:
        print(f"Error checking {table_name}: {str(e)}")

print(f"Using Supabase URL: {url}")
check_table("clients")
check_table("brands")
check_table("engineers")
check_table("site_contacts")
check_table("client_sites")
