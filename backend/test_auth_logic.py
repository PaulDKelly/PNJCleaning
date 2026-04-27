import os
import json
from workos import WorkOSClient
from dotenv import load_dotenv

load_dotenv('e:/Code/Projects/PNJCleaning/backend/.env')

def test_auth_logic():
    api_key = os.getenv('WORKOS_API_KEY')
    client_id = os.getenv('WORKOS_CLIENT_ID')
    redirect_uri = os.getenv('WORKOS_REDIRECT_URI')
    
    print(f"Using Redirect URI: {redirect_uri}")
    
    wos = WorkOSClient(api_key=api_key, client_id=client_id)
    
    email = "test@innovai.co.uk"
    domain = email.split('@')[-1]
    
    try:
        print(f"Step 1: Listing connections for domain '{domain}'...")
        connections = wos.sso.list_connections(domain=domain)
        if not connections.data:
            print(f"FAILURE: No connection found for domain '{domain}'")
            return
            
        connection_id = connections.data[0].id
        print(f"SUCCESS: Found connection '{connection_id}'")
        
        print("\nStep 2: Generating authorization URL (Checking 'state' as dict)...")
        try:
            # Current logic in auth.py uses state={}
            url = wos.sso.get_authorization_url(
                connection=connection_id,
                redirect_uri=redirect_uri,
                state={},
            )
            print(f"SUCCESS with dict: {url}")
        except Exception as dict_e:
            print(f"FAILURE with dict: {dict_e}")
            
            print("\nStep 3: Generating authorization URL (Checking 'state' as string)...")
            try:
                url = wos.sso.get_authorization_url(
                    connection=connection_id,
                    redirect_uri=redirect_uri,
                    state="test_state",
                )
                print(f"SUCCESS with string: {url}")
            except Exception as str_e:
                print(f"FAILURE with string: {str_e}")

    except Exception as e:
        print(f"TOP LEVEL ERROR: {e}")

if __name__ == "__main__":
    test_auth_logic()
