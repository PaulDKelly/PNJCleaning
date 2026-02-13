import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to find the app module
sys.path.append(os.path.abspath(os.curdir))

load_dotenv()

try:
    from app.supabase_client import supabase
    # Search for gmail emails
    res = supabase.table('users').select('id, username, email').ilike('email', '%gmail.com').execute()
    print("Gmail Users found:")
    for user in res.data:
        print(f"- ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
    if not res.data:
        print("No Gmail users found in the database.")
except Exception as e:
    print(f"Error: {e}")
