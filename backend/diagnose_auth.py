import os
import sys
from dotenv import load_dotenv

# Path setup to match app import
sys.path.append(os.getcwd())

print("--- DIAGNOSTIC START ---")
# 1. Check environment
env_path = os.path.join(os.getcwd(), ".env")
print(f"Checking for .env at: {env_path}")
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("Loaded .env successfully.")
else:
    print("CRITICAL: .env file NOT FOUND in current directory.")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
print(f"SUPABASE_URL: {url}")
print(f"SUPABASE_KEY exists: {bool(key)}")

# 2. Try App Logic
try:
    from app.main import get_user_by_email
    from app import security
    
    test_emails = ["admin@pnjcleaning.co.uk", "admin@pnjcleaning.com"]
    password_to_test = "password123"
    
    for email in test_emails:
        print(f"\nTesting Login for: {email}")
        user = get_user_by_email(email)
        if not user:
            print(f"[-] User {email} NOT FOUND in Supabase.")
            continue
            
        print(f"[+] User found. Username: {user.username}")
        # Test hash matching
        match = security.verify_password(password_to_test, user.password)
        if match:
            print("[+] PASSWORD MATCHES!")
        else:
            print("[-] PASSWORD MISMATCH!")
            print(f"    Stored hash start: {user.password[:15]}...")
            # Generate a fresh hash for comparison
            fresh_hash = security.get_password_hash(password_to_test)
            print(f"    Fresh hash for '{password_to_test}' start: {fresh_hash[:15]}...")

except Exception as e:
    import traceback
    print(f"\nCRITICAL ERROR DURING DIAGNOSTIC:\n{e}")
    traceback.print_exc()

print("\n--- DIAGNOSTIC END ---")
