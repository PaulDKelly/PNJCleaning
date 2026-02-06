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
        cols_to_add = ["brand", "site_name", "company", "address"]
        for col in cols_to_add:
            try:
                info = conn.execute(text(f"PRAGMA table_info(jobs)")).fetchall()
                existing_cols = [row[1] for row in info]
                if col not in existing_cols:
                    print(f"Adding column '{col}' to 'jobs' table...")
                    conn.execute(text(f"ALTER TABLE jobs ADD COLUMN {col} VARCHAR"))
            except Exception as e:
                print(f"Error processing column '{col}' for jobs: {str(e)}")

        # 2. Add 'archived' column to 'clients' table
        try:
            info = conn.execute(text(f"PRAGMA table_info(clients)")).fetchall()
            existing_cols = [row[1] for row in info]
            if "archived" not in existing_cols:
                print("Adding column 'archived' to 'clients' table...")
                conn.execute(text("ALTER TABLE clients ADD COLUMN archived BOOLEAN DEFAULT 0"))
        except Exception as e:
            print(f"Error processing 'archived' for clients: {str(e)}")

        # 3. Add 'archived' column to 'client_sites' table
        try:
            info = conn.execute(text(f"PRAGMA table_info(client_sites)")).fetchall()
            existing_cols = [row[1] for row in info]
            if "archived" not in existing_cols:
                print("Adding column 'archived' to 'client_sites' table...")
                conn.execute(text("ALTER TABLE client_sites ADD COLUMN archived BOOLEAN DEFAULT 0"))
        except Exception as e:
            print(f"Error processing 'archived' for client_sites: {str(e)}")

        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
