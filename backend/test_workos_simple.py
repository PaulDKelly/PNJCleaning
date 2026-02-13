import os
import workos
from workos import WorkOSClient
from dotenv import load_dotenv

load_dotenv()

workos_api_key = os.getenv("WORKOS_API_KEY") 
wos = WorkOSClient(api_key=workos_api_key)

try:
    print("\nListing connections...")
    connections = wos.sso.list_connections()
    print(f"SUCCESS! Found {len(connections.data)} connections.")
    for c in connections.data:
        # Check all available attributes on the connection object
        print(f"\nConnection ID: {c.id}")
        print(f"Name: {c.name}")
        print(f"Connection Type: {c.connection_type}")
        print(f"Organization ID: {getattr(c, 'organization_id', 'N/A')}")
        print(f"Domains: {getattr(c, 'domains', 'N/A')}")
except Exception as e:
    print(f"FAILURE: {e}")
