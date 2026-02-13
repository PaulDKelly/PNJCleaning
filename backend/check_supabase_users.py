import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment.")
    exit(1)

supabase: Client = create_client(url, key)

def list_users():
    try:
        res = supabase.table("users").select("*").execute()
        with open("supabase_users_debug.txt", "w") as f:
            if res.data:
                f.write(f"Found {len(res.data)} users:\n")
                for user in res.data:
                    f.write(f"Username: {user.get('username')}, Email: {user.get('email')}, Role: {user.get('role')}\n")
            else:
                f.write("No users found in Supabase.\n")
        print("Done. Results written to supabase_users_debug.txt")
    except Exception as e:
        print(f"Error querying Supabase: {e}")

if __name__ == "__main__":
    list_users()
