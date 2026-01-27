from sqlmodel import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pnj_database.db")
engine = create_engine(DATABASE_URL)

def migrate():
    with engine.connect() as conn:
        print(f"Connected to {DATABASE_URL}")
        
        # 1. Add missing columns to 'jobs' table
        # SQLite doesn't have "ADD COLUMN IF NOT EXISTS" for older versions, 
        # so we check pragma table_info
        cols_to_add = ["brand", "site_name", "company", "address"]
        
        for col in cols_to_add:
            try:
                # Check column info
                info = conn.execute(text(f"PRAGMA table_info(jobs)")).fetchall()
                existing_cols = [row[1] for row in info]
                
                if col not in existing_cols:
                    print(f"Adding column '{col}' to 'jobs' table...")
                    conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col} VARCHAR"))
                    print(f"Successfully added '{col}'.")
                else:
                    print(f"Column '{col}' already exists.")
            except Exception as e:
                print(f"Error processing column '{col}': {str(e)}")

        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
