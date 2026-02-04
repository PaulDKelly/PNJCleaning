import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    # Fail silently or logging? Ideally we should have these.
    # For now, let's just print a warning if imported but mostly we need them.
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment.")

supabase: Client = create_client(url, key)
