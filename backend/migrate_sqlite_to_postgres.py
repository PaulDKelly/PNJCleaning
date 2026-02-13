import os
import sys
from sqlmodel import create_engine, Session, select, SQLModel
from sqlalchemy import text
# Import all models to ensure they are registered with SQLModel
from app.models import Client, Engineer, SiteContact, Brand, ClientSite, Job, EngineerDiary, User, PasswordReset, ExtractionReport, ExtractionMicronReading, ExtractionPhoto, ExtractionInspectionItem, ExtractionFilterItem

def migrate_data():
    # 1. Source: SQLite
    sqlite_url = "sqlite:///./production.sqlite"
    if not os.path.exists("production.sqlite"):
        print("Error: production.sqlite not found. Make sure you have the source database.")
        sys.exit(1)
        
    print(f"Reading from: {sqlite_url}")
    sqlite_engine = create_engine(sqlite_url)

    # 2. Destination: Postgres
    # Try to get from args first, then env var
    pg_url = None
    if len(sys.argv) > 1:
        pg_url = sys.argv[1]
    else:
        pg_url = os.getenv("DATABASE_URL")
        
    if not pg_url or "sqlite" in pg_url:
        print("Error: Target DATABASE_URL not provided or valid.")
        print("Usage: python migrate_sqlite_to_postgres.py <postgres_connection_string>")
        sys.exit(1)

    # Fix: Ensure URL starts with postgresql:// (SQLAlchemy 1.4+ deprecated postgres://)
    if pg_url.startswith("postgres://"):
        pg_url = pg_url.replace("postgres://", "postgresql://", 1)
        
    print(f"Writing to: {pg_url.split('@')[1] if '@' in pg_url else 'Postgres DB'}") # Hide auth info
    pg_engine = create_engine(pg_url)

    # 3. Create Tables in Postgres
    print("Creating tables in destination database...")
    SQLModel.metadata.create_all(pg_engine)

    # 4. Transfer Data
    tables_to_migrate = [
        User, Client, Engineer, SiteContact, Brand, ClientSite, Job, 
        EngineerDiary, PasswordReset, ExtractionReport, 
        ExtractionMicronReading, ExtractionPhoto, ExtractionInspectionItem, ExtractionFilterItem
    ]
    
    with Session(sqlite_engine) as source_session, Session(pg_engine) as target_session:
        for model in tables_to_migrate:
            table_name = model.__tablename__
            print(f"Migrating table: {table_name}...", end=" ", flush=True)
            
            # Fetch all records from source
            records = source_session.exec(select(model)).all()
            count = 0
            
            for record in records:
                # We need to detach the instance from the source session and add to target
                # The easiest way is to expunge it or create a new instance with same data
                # SQLModel/Pydantic makes this easy with model_dump()
                data = record.model_dump()
                new_record = model(**data)
                
                # Check for duplicates or conflicts? 
                # For clean migration, we assume empty target or we just upsert.
                # Here we'll try simple add. If ID exists, it might fail if we don't handle it.
                # Assuming empty destination for now.
                target_session.add(new_record)
                count += 1
                
            print(f"Done! ({count} records)")
            
        try:
            target_session.commit()
            print("\nMigration completed successfully!")
        except Exception as e:
            target_session.rollback()
            print(f"\nError committing changes: {e}")
            sys.exit(1)

if __name__ == "__main__":
    migrate_data()
