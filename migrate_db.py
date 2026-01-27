import sys
import os
from sqlmodel import SQLModel, create_engine

# Add backend to path to import models and database
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Explicitly use the engine with the correct path
sqlite_url = "sqlite:///backend/pnj_database.db"
engine = create_engine(sqlite_url)

from app.models import SQLModel, Job, ExtractionReport, ExtractionMicronReading, ExtractionInspectionItem, ExtractionFilterItem, User, Client, Engineer, SiteContact

def migrate():
    print("Dropping existing tables to fix schema mismatch...")
    SQLModel.metadata.drop_all(engine)
    print("Recreating tables with new unified schema...")
    SQLModel.metadata.create_all(engine)
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
