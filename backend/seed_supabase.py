from app.supabase_client import supabase
from app import security

# Create admin user
hashed_password = security.get_password_hash("admin123")

# Check if admin exists
existing = supabase.table("users").select("*").eq("username", "admin").execute()

if existing.data:
    print("Admin user already exists.")
else:
    # Insert admin user
    result = supabase.table("users").insert({
        "username": "admin",
        "email": "admin@pnjcleaning.com",
        "password": hashed_password
    }).execute()
    
    if result.data:
        print("✅ Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("❌ Failed to create admin user")
        print(result)
