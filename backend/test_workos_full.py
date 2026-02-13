import os
from workos import WorkOSClient
from dotenv import load_dotenv

load_dotenv()

workos_api_key = os.getenv("WORKOS_API_KEY") 
workos_client_id = os.getenv("WORKOS_CLIENT_ID")
workos_redirect_uri = os.getenv("WORKOS_REDIRECT_URI")

print(f"Testing with Client ID: {workos_client_id}")
print(f"Testing with API Key Prefix: {workos_api_key[:15]}... (Length: {len(workos_api_key)})")

wos = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)

try:
    print("\nStep 1: Listing connections for domain 'innovai.co.uk'...")
    connections = wos.sso.list_connections(domain="innovai.co.uk")
    
    if not connections.data:
        print("FAILURE: No connections found for domain 'innovai.co.uk'.")
        # Fallback to general list to see if ANYTHING is there
        print("Trying to list all connections...")
        all_conns = wos.sso.list_connections()
        print(f"Found {len(all_conns.data)} total connections.")
        for c in all_conns.data:
             print(f"- {c.id} ({c.name})")
    else:
        conn = connections.data[0]
        print(f"SUCCESS: Found connection {conn.id} ({conn.name})")
        
        print("\nStep 2: Getting authorization URL...")
        auth_url = wos.sso.get_authorization_url(
            connection=conn.id,
            redirect_uri=workos_redirect_uri,
            state={},
        )
        print(f"SUCCESS: {auth_url}")
except Exception as e:
    print(f"FAILURE: {e}")
