import os
import requests
from dotenv import load_dotenv

load_dotenv()

workos_api_key = os.getenv("WORKOS_API_KEY") 
workos_client_id = os.getenv("WORKOS_CLIENT_ID")
redirect_uri = os.getenv("WORKOS_REDIRECT_URI")

# The connection ID we found manually
connection_id = "conn_01KGSFCBE25DDPB02K52HSRWK0"

print(f"Testing Initiation with Client ID: {workos_client_id}")

# In WorkOS, initiation is just building a URL for the browser.
# But you can also test it by hitting the API if you use the SDK's internal logic.
# Actually, let's just use the SDK now that we know the API key is valid.

from workos import WorkOSClient
wos = WorkOSClient(api_key=workos_api_key, client_id=workos_client_id)

try:
    print(f"\nTrying to get auth URL for connection {connection_id}...")
    auth_url = wos.sso.get_authorization_url(
        connection=connection_id,
        redirect_uri=redirect_uri,
        state={},
    )
    print(f"SUCCESS! Auth URL: {auth_url}")
except Exception as e:
    print(f"FAILURE: {e}")

try:
    print(f"\nTrying to get auth URL for domain 'innovai.co.uk' (expect failure)...")
    # Using 'domain' since the SDK help said it's not a direct param, 
    # but maybe it can be passed in kwargs? No, we saw 'unexpected keyword argument'.
    # So we'll try 'organization' or 'connection'.
    auth_url = wos.sso.get_authorization_url(
        organization="org01", # fake org
        redirect_uri=redirect_uri,
    )
except Exception as e:
    print(f"FAILURE (expected): {e}")
