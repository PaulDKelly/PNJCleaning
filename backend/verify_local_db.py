from sqlmodel import Session, create_engine, select, text
from app.models import Client, Engineer, Job
import os

# Point directly to the file in the current directory
db_path = "pnj_database.db"
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found!")
    exit(1)

engine = create_engine(f"sqlite:///{db_path}")

try:
    with Session(engine) as session:
        clients = session.exec(select(Client)).all()
        engineers = session.exec(select(Engineer)).all()
        jobs = session.exec(select(Job)).all()
        
        print(f"Database File: {os.path.abspath(db_path)}")
        print(f"Size: {os.path.getsize(db_path)} bytes")
        print("-" * 20)
        print(f"Clients count: {len(clients)}")
        for c in clients:
            print(f" - {c.client_name}")
            
        print("-" * 20)
        print(f"Engineers count: {len(engineers)}")
        for e in engineers:
            print(f" - {e.contact_name}")

        print("-" * 20)
        print(f"Jobs count: {len(jobs)}")
except Exception as e:
    print(f"Error reading database: {e}")
