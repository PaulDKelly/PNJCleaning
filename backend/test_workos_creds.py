import os
import workos
from workos import client as workos_client
from dotenv import load_dotenv

load_dotenv()

workos.api_key = os.getenv("WORKOS_API_KEY")
workos.client_id = os.getenv("WORKOS_CLIENT_ID")
redirect_uri = os.getenv("WORKOS_REDIRECT_URI")

print(f"Testing with Client ID: {workos.client_id}")
print(f"Testing with API Key: {workos.api_key[:10]}...")
print(f"Redirect URI: {redirect_uri}")

try:
    authorization_url = workos_client.sso.get_authorization_url(
        domain="innovai.co.uk",
        redirect_uri=redirect_uri,
        state={},
    )
    print(f"\nSUCCESS! Authorization URL: {authorization_url}")
except Exception as e:
    print(f"\nFAILURE: {e}")
