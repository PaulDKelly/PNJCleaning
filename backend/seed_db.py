from sqlmodel import Session
from app.database import engine, init_db
from app.models import Client, Engineer, JobSchedule, User
from app import security
from datetime import date, time

def seed_data():
    init_db()
    with Session(engine) as session:
        # Check if already seeded
        if session.query(User).first():
            print("Database already seeded.")
            return

        print("Seeding database...")
        
        # Add a default admin user
        admin_user = User(
            username="admin",
            email="admin@pnjcleaning.com",
            password=security.get_password_hash("admin123")
        )
        session.add(admin_user)
        
        # Add Clients
        c1 = Client(client_name="Client A", company="Company Alpha", address="123 Alpha St")
        c2 = Client(client_name="Client B", company="Company Beta", address="456 Beta Ave")
        session.add(c1)
        session.add(c2)
        
        # Add Engineers
        e1 = Engineer(contact_name="John Doe", email="john@example.com", phone="0123456789")
        e2 = Engineer(contact_name="Jane Smith", email="jane@example.com", phone="9876543210")
        session.add(e1)
        session.add(e2)
        
        # Add Job Schedules
        js1 = JobSchedule(
            job_number="JN001", 
            client_name="Client A", 
            date=date(2025, 6, 24), 
            time=time(9, 0), 
            status="Scheduled",
            notes="Regular maintenance"
        )
        js2 = JobSchedule(
            job_number="JN002", 
            client_name="Client B", 
            date=date(2025, 6, 25), 
            time=time(14, 30), 
            status="Completed",
            notes="Emergency repair"
        )
        session.add(js1)
        session.add(js2)
        
        session.commit()
        print("Seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
