from sqlmodel import Session, create_engine, select
import sys
import os

# Add backend to path to import models
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import models
from app.security import get_password_hash
from datetime import date, time, datetime

engine = create_engine('sqlite:///backend/pnj_database.db')

with Session(engine) as session:
    # 1. Create Default Admin User
    admin = session.exec(select(models.User).where(models.User.username == "pnj_admin")).first()
    if not admin:
        admin = models.User(
            username="pnj_admin",
            email="admin@pnjcleaning.co.uk",
            password=get_password_hash("pnj_pass")
        )
        session.add(admin)
        print("Created admin user")

    # 2. Create Engineer
    eng = session.exec(select(models.Engineer).where(models.Engineer.contact_name == "pnj_admin")).first()
    if not eng:
        eng = models.Engineer(contact_name="pnj_admin", email="admin@pnjcleaning.co.uk", phone="0123456789")
        session.add(eng)
        print("Created engineer profile")

    # 3. Create Client
    client = session.exec(select(models.Client).where(models.Client.client_name == "Test Client")).first()
    if not client:
        client = models.Client(client_name="Test Client", company="The Grill House", address="123 High St, London")
        session.add(client)
        print("Created client")

    session.commit()

    # 4. Create Job
    job = models.Job(
        job_number="JN-001",
        date=date.today(),
        time=time(10, 0),
        priority="High",
        status="Scheduled",
        client_name="Test Client",
        engineer_contact_name="pnj_admin",
        address="123 High St, London",
        notes="Urgent kitchen extract clean"
    )
    session.add(job)
    print("Created job JN-001")

    # 5. Create Report for another job
    report = models.ExtractionReport(
        job_number='JN-002',
        company='The Grill House',
        date=date.today(),
        time=time(14,0),
        address='123 High St, London',
        contact_name='John Doe',
        contact_number='0123456789',
        status='Submitted',
        risk_pre=3,
        risk_post=1,
        cleaning_interval_recommended='6 Months',
        engineer_signature="pnj_admin"
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    
    m1 = models.ExtractionMicronReading(
        report_id=report.id,
        location='T1',
        description='Canopy',
        pre_clean=350,
        post_clean=10
    )
    session.add(m1)
    
    i1 = models.ExtractionInspectionItem(
        report_id=report.id,
        item_name='Main Ducting',
        pass_status=True,
        advice='All good'
    )
    session.add(i1)
    
    session.commit()
    print(f"Created report ID: {report.id} for job JN-002")
