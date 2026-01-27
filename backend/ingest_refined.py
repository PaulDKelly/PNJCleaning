import pandas as pd
import uuid
from sqlmodel import Session, select
from app.database import engine
from app import models

KNOWN_BRANDS = ["KFC", "Taco Bell", "Pizza Hut", "McDonald's", "Burger King", "Subway", "Starbucks", "Costa", "Greggs", "Dominos"]

def get_brand(site_name):
    if not site_name: return None
    for brand in KNOWN_BRANDS:
        if brand.lower() in str(site_name).lower():
            return brand
    return None

def ingest_refined_clients():
    print("\n--- Refining Client and Site Ingestion (Phase 10b) ---")
    file_path = "e:/Code/Projects/PNJCleaning/All Stores Spreadsheet.xlsx"
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    
    ambiguous_data = []

    with Session(engine) as session:
        for index, row in df.iterrows():
            # Based on mapping:
            # Col 2: Site Name
            # Col 3: Address
            # Col 4: Postcode
            # Col 5: Company / Client Name
            
            site_raw = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None
            address = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            postcode = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
            company_raw = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else None
            
            if not site_raw or site_raw in ['nan', 'SME Pizza Hut', 'Store Name']:
                 continue

            brand_name = get_brand(site_raw)
            
            # Decide the Client Name (Franchisee or Brand or Independent)
            # If we have a company name (Col 5), that is our Client.
            # If not, use the Brand. 
            # If neither, it's an Independent.
            
            final_client_name = company_raw if company_raw else (brand_name if brand_name else "Independent")
            
            # If it's truly ambiguous (no company and no brand), flag it
            if not company_raw and not brand_name:
                ambiguous_data.append({
                    "row": index,
                    "site": site_raw,
                    "address": address,
                    "postcode": postcode,
                    "original_col5": row.iloc[5]
                })

            # 1. Ensure Brand exists
            if brand_name:
                existing_brand = session.exec(select(models.Brand).where(models.Brand.brand_name == brand_name)).first()
                if not existing_brand:
                    print(f"Adding Brand: {brand_name}")
                    new_brand = models.Brand(brand_name=brand_name)
                    session.add(new_brand)
                    session.commit()

            # 2. Ensure Client exists
            existing_client = session.exec(select(models.Client).where(models.Client.client_name == final_client_name)).first()
            if not existing_client:
                print(f"Adding Client: {final_client_name}")
                new_client = models.Client(
                    client_name=final_client_name,
                    company=final_client_name if company_raw else None,
                    portal_token=str(uuid.uuid4())
                )
                session.add(new_client)
                session.commit()

            # 3. Add Site
            existing_site = session.exec(select(models.ClientSite).where(
                models.ClientSite.client_name == final_client_name,
                models.ClientSite.site_name == site_raw
            )).first()
            
            if not existing_site:
                print(f"Adding Site: {site_raw} (Client: {final_client_name})")
                full_address = f"{address} {postcode}".strip()
                new_site = models.ClientSite(
                    client_name=final_client_name,
                    site_name=site_raw,
                    address=full_address,
                    brand_name=brand_name
                )
                session.add(new_site)
        
        session.commit()

    if ambiguous_data:
        print(f"\nFound {len(ambiguous_data)} ambiguous records. Saving to data_dump.csv...")
        dump_df = pd.DataFrame(ambiguous_data)
        dump_df.to_csv("e:/Code/Projects/PNJCleaning/backend/data_dump.csv", index=False)
        print("Data dump created at backend/data_dump.csv")

if __name__ == "__main__":
    ingest_refined_clients()
    print("\nRefined Ingestion Complete.")
