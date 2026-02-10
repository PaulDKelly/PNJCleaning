import os
import requests
from dotenv import load_dotenv

load_dotenv()

workos_api_key = os.getenv("WORKOS_API_KEY") 

headers = {
    "Authorization": f"Bearer {workos_api_key}"
}

try:
    response = requests.get("https://api.workos.com/connections", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"Status Code: 200")
        for c in data['data']:
            print(f"--- Connection ---")
            print(f"ID: {c['id']}")
            print(f"Name: {c['name']}")
            print(f"Type: {c['connection_type']}")
            print(f"Domains: {c.get('domains', [])}")
except Exception as e:
    print(f"Error: {e}")
