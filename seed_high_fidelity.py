from sqlmodel import Session, create_engine, select
import sys
import os

# Add backend to path to import models
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app import models
from app.security import get_password_hash
from datetime import date, time, datetime

engine = create_engine('sqlite:///backend/pnj_database.db')

def seed():
    with Session(engine) as session:
        # 1. Ensure Client exists
        client = session.exec(select(models.Client).where(models.Client.client_name == "Chuck and Blade")).first()
        if not client:
            client = models.Client(
                client_name="Chuck and Blade",
                company="Chuck and Blade",
                address="Dolphin Centre, Poole"
            )
            session.add(client)
        
        # 2. Ensure Engineer exists
        eng = session.exec(select(models.Engineer).where(models.Engineer.contact_name == "Gary Kelly")).first()
        if not eng:
            eng = models.Engineer(contact_name="Gary Kelly", email="gary@pnjcleaning.co.uk", phone="+44 758 512 7242")
            session.add(eng)
        
        session.commit()

        # 3. Create the High-Fidelity Job
        job_num = "JN-08012026"
        existing_job = session.exec(select(models.Job).where(models.Job.job_number == job_num)).first()
        if existing_job:
            session.delete(existing_job)
            session.commit()
            
        job = models.Job(
            job_number=job_num,
            date=date(2026, 1, 8),
            time=time(9, 0),
            priority="High",
            status="Completed",
            client_name="Chuck and Blade",
            engineer_contact_name="Gary Kelly",
            address="Dolphin Centre, Poole",
            brand="Chuck and Blade",
            notes="Full system audit and clean"
        )
        session.add(job)
        session.commit()

        # 4. Create the High-Fidelity Extraction Report
        report = models.ExtractionReport(
            job_number=job_num,
            company="Chuck and Blade",
            brand="Chuck and Blade",
            date=date(2026, 1, 8),
            time=time(9, 0),
            address="Dolphin Centre, Poole",
            contact_name="Manager",
            contact_number="01234 567890",
            status="Approved",
            risk_pre=3,
            risk_post=1,
            remedial_requirements="Baffle filters need cleaning weekly at least. In poor condition. Riser/duct run has no hatches.",
            risk_improvements="Next clean scheduled for April 2026.",
            sketch_details="Main Canopies and Ducting. Chipper canopy ducting and main ducting inside store. Attenuator not accessible.",
            cleaning_interval_current="6 Months",
            cleaning_interval_recommended="3 Months",
            engineer_signature="Gary Kelly",
            client_signature="Verified on site"
        )
        session.add(report)
        session.commit()
        session.refresh(report)

        # 5. Add Micron Readings (Table 12 from DOCX)
        readings = [
            ("T1", "Canopy/Extract Filters", 350, 0),
            ("T1.2", "Chipper Canopy", 350, 0),
            ("T2", "Main Duct", 300, 0),
            ("T2.2", "Chipper Duct", 300, 0),
            ("T3", "Ducting 3 meters from Canopy ESP", 300, 0),
            ("T5", "Ducting before Fan", 300, 0),
            ("T6", "Ducting after Fan", 300, 0)
        ]
        for loc, desc, pre, post in readings:
            m = models.ExtractionMicronReading(
                report_id=report.id,
                location=loc,
                description=desc,
                pre_clean=pre,
                post_clean=post
            )
            session.add(m)

        # 6. Add Inspection Items (Table 10 from DOCX)
        items = [
            ("All cooker canopies and Grease traps", True, "Compliant. Baffle filters need cleaning weekly at least. In poor condition."),
            ("Extraction Ducting (accessible via hatches)", True, "Compliant"),
            ("Extraction fan and housing", True, "Compliant"),
            ("Duct run", True, "Compliant"),
            ("Riser/duct run", False, "Risers have no hatches. Also not easily accessible", True), # Fail/Issue
            ("Activated carbon", False, "N/A"),
            ("ESP Filters", False, "N/A"),
            ("Ozone filters", False, "N/A"),
            ("Attenuator (silencers)", True, "Good condition but not accessible for full clean"),
        ]
        for name, pass_st, advice, *extra in items:
            fail_st = extra[0] if extra else False
            ii = models.ExtractionInspectionItem(
                report_id=report.id,
                item_name=name,
                pass_status=pass_st,
                fail_status=fail_st,
                advice=advice
            )
            session.add(ii)

        # 7. Add Filter Inventory
        fi = models.ExtractionFilterItem(
            report_id=report.id,
            filter_type="Stainless Steel Baffle",
            quantity=1,
            pass_status=False, # Poor condition
            fail_status=True
        )
        session.add(fi)

        # 8. Add Photos (Using extracted images - 8 photos for 2 pages)
        photo_dir = r"E:\Code\Projects\PNJCleaning\backend\app\static\images"
        photo_samples = [
            ("Before", os.path.join(photo_dir, "image_3.jpeg"), "Main Canopy Initial Build-up"),
            ("After", os.path.join(photo_dir, "image_5.jpeg"), "Main Canopy Post-Clean"),
            ("Before", os.path.join(photo_dir, "image_6.jpeg"), "Extract Plenum (Pre)"),
            ("After", os.path.join(photo_dir, "image_7.jpeg"), "Extract Plenum (Post)"),
            ("Before", os.path.join(photo_dir, "image_8.jpeg"), "Filter Condition (Inner)"),
            ("After", os.path.join(photo_dir, "image_9.jpeg"), "Filter Track Post-Service"),
            ("Before", os.path.join(photo_dir, "image_10.jpeg"), "Fan Assembly Housing"),
            ("After", os.path.join(photo_dir, "image_11.jpeg"), "Fan Blades Cleaned"),
        ]
        for p_type, p_path, p_item in photo_samples:
            photo = models.ExtractionPhoto(
                report_id=report.id,
                photo_type=p_type,
                photo_path=p_path,
                inspection_item=p_item
            )
            session.add(photo)

        session.commit()
        print(f"Successfully seeded high-fidelity report ID: {report.id} for JN-08012026")

if __name__ == "__main__":
    seed()
