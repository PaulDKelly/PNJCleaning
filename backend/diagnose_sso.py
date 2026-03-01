import os
import json
from workos import WorkOSClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('e:/Code/Projects/PNJCleaning/backend/.env')

def diagnose_sso():
    api_key = os.getenv('WORKOS_API_KEY')
    client_id = os.getenv('WORKOS_CLIENT_ID')
    
    print("--- WorkOS SSO Diagnostic Tool ---")
    print(f"API Key: {api_key[:10]}...{api_key[-5:] if api_key else ''}")
    print(f"Client ID: {client_id}")
    
    if not api_key or not client_id:
        print("ERROR: Missing WORKOS_API_KEY or WORKOS_CLIENT_ID in .env")
        return

    wos = WorkOSClient(api_key=api_key, client_id=client_id)
    
    try:
        # Check Environment
        if api_key.startswith("sk_test_"):
            print("Environment: WorkOS TEST Environment")
        elif api_key.startswith("sk_live_"):
            print("Environment: WorkOS LIVE Environment")
        else:
            print("Environment: Unknown (Check API Key format)")

        print("\n--- Listing Organizations ---")
        orgs = wos.organizations.list_organizations()
        if not orgs.data:
            print("No Organizations found.")
        else:
            for org in orgs.data:
                print(f"Org: {org.name} ({org.id})")
                print(f"  Domains: {[d.domain for d in org.domains]}")

        print("\n--- Listing ALL Connections ---")
        # Explicitly list ALL connections without domain filter
        connections = wos.sso.list_connections()
        
        if not connections.data:
            print("No connections found at all via API.")
        else:
            print(f"Found {len(connections.data)} connection(s):")
            for conn in connections.data:
                print(f"\n- Connection: '{conn.name}'")
                print(f"  ID: {conn.id}")
                print(f"  Type: {conn.connection_type}")
                print(f"  State: {conn.state}")
                print(f"  Org ID: {conn.organization_id}")
                # Fetch domains for this specific connection if not in objects
                # Note: conn.domains is usually a list of Domain objects
                domains = [d.domain for d in getattr(conn, 'domains', [])]
                print(f"  Domains mapped: {domains}")
                
                if not domains:
                    print("  WARNING: This connection has NO domains mapped. It will not work with domain-based login.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    diagnose_sso()
