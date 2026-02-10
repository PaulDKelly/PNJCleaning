import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to find the app module
sys.path.append(os.path.abspath(os.curdir))

load_dotenv()

try:
    from app.supabase_client import supabase
    res = supabase.table('users').select('username, email').execute()
    with open('users_list_utf8.txt', 'w', encoding='utf-8') as f:
        f.write("Database Users:\n")
        for user in res.data:
            f.write(f"Username: {user['username']}, Email: {user['email']}\n")
    print("Successfully wrote to users_list_utf8.txt")
except Exception as e:
    print(f"Error: {e}")
