from app.supabase_client import supabase
import secrets

# Create a test client with portal token
portal_token = secrets.token_urlsafe(32)

# Check if test client exists
existing = supabase.table("clients").select("*").eq("client_name", "Test Client").execute()

if existing.data:
    # Update existing client with portal token
    result = supabase.table("clients").update({
        "portal_token": portal_token
    }).eq("client_name", "Test Client").execute()
    print(f"✅ Updated existing Test Client")
else:
    # Create new test client
    result = supabase.table("clients").insert({
        "client_name": "Test Client",
        "company": "Test Company Ltd",
        "address": "123 Test Street, Test City",
        "portal_token": portal_token
    }).execute()
    print(f"✅ Created Test Client")

print(f"\n🔗 Portal URL: http://pnj-backend-aci.uksouth.azurecontainer.io:8000/portal/{portal_token}")
print(f"\n📋 Portal Token: {portal_token}")
