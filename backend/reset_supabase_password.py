import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.getcwd())
from app.security import get_password_hash

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment.")
    exit(1)

supabase: Client = create_client(url, key)

def reset_password(email, new_password):
    try:
        hashed_pw = get_password_hash(new_password)
        res = supabase.table("users").update({"password": hashed_pw}).eq("email", email).execute()
        if res.data:
            print(f"Password for {email} reset successfully.")
        else:
            print(f"User with email {email} not found.")
    except Exception as e:
        print(f"Error resetting password: {e}")

if __name__ == "__main__":
    email_to_reset = "admin@pnjcleaning.co.uk"
    new_pw = "password123"
    reset_password(email_to_reset, new_pw)
