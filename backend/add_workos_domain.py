import os
from workos import WorkOSClient
from dotenv import load_dotenv

load_dotenv('e:/Code/Projects/PNJCleaning/backend/.env')

def add_domain():
    api_key = os.getenv('WORKOS_API_KEY')
    client_id = os.getenv('WORKOS_CLIENT_ID')
    org_id = "org_01KGEVH0PVWC8PFYXGR0W8XYQ0"  # Ingenaium Org ID
    domain = "innovai.co.uk"

    wos = WorkOSClient(api_key=api_key, client_id=client_id)
    
    try:
        print(f"Adding domain '{domain}' to organization '{org_id}'...")
        # Correct v4+ method
        result = wos.organization_domains.create_organization_domain(
            organization_id=org_id,
            domain=domain
        )
        print(f"SUCCESS: Domain added. ID: {getattr(result, 'id', 'N/A')}")
        
        # Verify
        org = wos.organizations.get_organization(org_id)
        print(f"Current Domains in Org: {[d.domain for d in org.domains]}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    add_domain()
