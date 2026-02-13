import os
import sys
from dotenv import load_dotenv

# Path setup to match app import
sys.path.append(os.getcwd())
load_dotenv()

from app.security import get_password_hash, verify_password
from app.main import get_user_by_email
from app.supabase_client import supabase

def force_reset_and_verify(email, password):
    print(f"\n--- TESTING {email} ---")
    
    # 1. Generate new hash
    new_hash = get_password_hash(password)
    print(f"Generated hash: {new_hash[:20]}...")
    
    # 2. Update Supabase
    print("Updating Supabase...")
    res = supabase.table("users").update({"password": new_hash}).eq("email", email).execute()
    
    if not res.data:
        print(f"[-] FAILED: No user updated for email {email}")
        return
    
    print(f"[+] Successfully updated {len(res.data)} record(s).")
    
    # 3. Verify via Supabase Fetch
    print("Fetching user back from Supabase...")
    user = get_user_by_email(email)
    if not user:
        print("[-] FAILED: Could not fetch user back.")
        return
        
    print(f"Stored hash in DB starts with: {user.password[:20]}...")
    
    # 4. Verify Password
    match = verify_password(password, user.password)
    if match:
        print("[+] VERIFICATION SUCCESSFUL!")
    else:
        print("[-] VERIFICATION FAILED after reset!")

if __name__ == "__main__":
    pw = "password123"
    force_reset_and_verify("admin@pnjcleaning.co.uk", pw)
    force_reset_and_verify("admin@pnjcleaning.com", pw)
