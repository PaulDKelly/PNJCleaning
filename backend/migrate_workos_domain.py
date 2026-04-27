import os
from workos import WorkOSClient

old_key = os.getenv("WORKOS_OLD_API_KEY")
old_client_id = os.getenv("WORKOS_OLD_CLIENT_ID")
new_key = os.getenv("WORKOS_NEW_API_KEY")
new_client_id = os.getenv("WORKOS_NEW_CLIENT_ID")
domain_to_free = os.getenv("WORKOS_DOMAIN_TO_FREE", "innovai.co.uk")
new_org_id = os.getenv("WORKOS_NEW_ORG_ID")

def clean_and_map():
    if not all([old_key, old_client_id, new_key, new_client_id, new_org_id]):
        raise RuntimeError(
            "Missing required env vars: WORKOS_OLD_API_KEY, WORKOS_OLD_CLIENT_ID, "
            "WORKOS_NEW_API_KEY, WORKOS_NEW_CLIENT_ID, WORKOS_NEW_ORG_ID"
        )

    # 1. Try to find the domain in the OLD project
    print(f"Checking OLD project for domain '{domain_to_free}'...")
    w_old = WorkOSClient(api_key=old_key, client_id=old_client_id)
    try:
        orgs = w_old.organizations.list_organizations()
        for org in orgs.data:
            if domain_to_free in [d.domain for d in org.domains]:
                print(f"Found domain in Org: {org.name} ({org.id})")
                # Find the domain ID
                domain_id = [d.id for d in org.domains if d.domain == domain_to_free][0]
                print(f"Deleting domain {domain_id} from OLD org...")
                w_old.organization_domains.delete_organization_domain(domain_id)
                print("SUCCESS: Domain freed from OLD project.")
    except Exception as e:
        print(f"Error checking old project: {e}")

    # 2. Add it to the NEW project
    print(f"\nAdding domain '{domain_to_free}' to NEW project...")
    w_new = WorkOSClient(api_key=new_key, client_id=new_client_id)
    try:
        result = w_new.organization_domains.create_organization_domain(
            organization_id=new_org_id,
            domain=domain_to_free
        )
        print(f"SUCCESS: Domain added to Ingenaium. ID: {getattr(result, 'id', 'N/A')}")
    except Exception as e:
        print(f"Error adding to new project: {e}")

if __name__ == "__main__":
    clean_and_map()
