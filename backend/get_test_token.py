
import os
from supabase import create_client

# Hardcoded for quick check based on deploy_aca.ps1 logs/content
url = "https://ruaseemcgxvbcjazhhfw.supabase.co"
key = "sb_publishable_dPA9xqq4yyGg6869fCuMLA_tCXIKXOu" # Service role key would be better but this is pub key

supabase = create_client(url, key)

def get_token():
    try:
        # Try to get Paul Kelly
        res = supabase.table("engineers").select("contact_name, access_token").ilike("contact_name", "%Paul Kelly%").execute()
        if res.data:
            print(f"Found {len(res.data)} engineers matching 'Paul Kelly'.")
            for eng in res.data:
                print(f"Name: {eng['contact_name']}")
                print(f"Token: {eng['access_token']}")
                print("-" * 20)
        else:
            print("No engineer found matching 'Paul Kelly'. Fetching all to check names...")
            all_res = supabase.table("engineers").select("contact_name").execute()
            for e in all_res.data:
                print(e['contact_name'])
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_token()
