import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to find the app module
sys.path.append(os.path.abspath(os.curdir))

load_dotenv()

try:
    from app.supabase_client import supabase
    res = supabase.table('users').select('username, email').execute()
    print("Database Users:")
    for user in res.data:
        print(f"Username: {user['username']}, Email: {user['email']}")
except Exception as e:
    print(f"Error: {e}")
