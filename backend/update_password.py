from app.supabase_client import supabase
from app.security import get_password_hash
import json

def update_password():
    email = "admin@pnjcleaning.co.uk"
    new_password = "password123"
    hashed = get_password_hash(new_password)
    
    res = supabase.table("users").update({"password": hashed}).eq("email", email).execute()
    if res.data:
        print(f"SUCCESS: Updated password for {email}")
    else:
        print(f"FAILED: User {email} not found")

if __name__ == "__main__":
    update_password()
