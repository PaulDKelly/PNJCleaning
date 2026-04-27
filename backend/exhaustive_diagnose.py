import os
from workos import WorkOSClient
from dotenv import load_dotenv

load_dotenv('e:/Code/Projects/PNJCleaning/backend/.env')

def exhaustive_diagnose():
    api_key = os.getenv('WORKOS_API_KEY')
    client_id = os.getenv('WORKOS_CLIENT_ID')
    
    print(f"DEBUG: API Key starting with: {api_key[:10]}...")
    print(f"DEBUG: Client ID: {client_id}")
    
    env_type = "TEST" if api_key.startswith("sk_test") else "LIVE"
    print(f"Environment detected from key: {env_type}")
    
    wos = WorkOSClient(api_key=api_key, client_id=client_id)
    
    print("\n--- Listing ALL Organizations ---")
    orgs = wos.organizations.list_organizations()
    for org in orgs.data:
        print(f"Org Name: {org.name}")
        print(f"Org ID: {org.id}")
        print(f"Org Domains: {[d.domain for d in org.domains]}")
        print("-" * 20)
        
    print("\n--- Listing ALL Connections ---")
    conns = wos.sso.list_connections()
    print(f"Total Connections Found: {len(conns.data)}")
    for conn in conns.data:
        print(f"Connection Name: {conn.name}")
        print(f"Connection ID: {conn.id}")
        print(f"Status: {conn.state}")
        print(f"Domains: {[d.domain for d in getattr(conn, 'domains', [])]}")
        print(f"Organization ID: {conn.organization_id}")
        print("-" * 20)

if __name__ == "__main__":
    exhaustive_diagnose()
