import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to find the app module
sys.path.append(os.path.abspath(os.curdir))

load_dotenv()

try:
    from app.supabase_client import supabase
    # Search for paul in username or email
    res = supabase.table('users').select('id, username, email').or_(f"username.ilike.%paul%,email.ilike.%paul%").execute()
    print("Users found matching 'paul':")
    for user in res.data:
        print(f"- ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
    if not res.data:
        print("No users matching 'paul' found.")
except Exception as e:
    print(f"Error: {e}")
