from sqlmodel import Session, text
from app.database import engine

def cleanup_clients():
    print("--- Cleaning up Client, Site, and Brand data ---")
    with Session(engine) as session:
        try:
            # We need to delete in order of dependencies
            print("Deleting Client Sites...")
            session.exec(text("DELETE FROM client_sites"))
            
            print("Deleting Clients...")
            session.exec(text("DELETE FROM clients"))
            
            print("Deleting Brands...")
            session.exec(text("DELETE FROM brands"))
            
            session.commit()
            print("Cleanup complete.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            session.rollback()

if __name__ == "__main__":
    cleanup_clients()
