import os
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("WORKOS_CLIENT_ID")
api_key = os.getenv("WORKOS_API_KEY")

def debug_string(name, val):
    if val is None:
        print(f"{name}: None")
        return
    print(f"{name}: '{val}' (Length: {len(val)})")
    print(f"{name} Hex: {val.encode('utf-8').hex()}")

debug_string("WORKOS_CLIENT_ID", client_id)
debug_string("WORKOS_API_KEY", api_key)
