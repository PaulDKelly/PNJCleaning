import uuid
from datetime import date, time, datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

class Client(SQLModel, table=True):
    __tablename__ = "clients"
    client_name: str = Field(primary_key=True)
    company: Optional[str] = None
    address: Optional[str] = None
    portal_token: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True, unique=True)
    portal_enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Engineer(SQLModel, table=True):
    __tablename__ = "engineers"
    contact_name: str = Field(primary_key=True)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SiteContact(SQLModel, table=True):
    __tablename__ = "site_contacts"
    contact_name: str = Field(primary_key=True)
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Brand(SQLModel, table=True):
    __tablename__ = "brands"
    id: Optional[int] = Field(default=None, primary_key=True)
    brand_name: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ClientSite(SQLModel, table=True):
    __tablename__ = "client_sites"
    id: Optional[int] = Field(default=None, primary_key=True)
    client_name: str = Field(foreign_key="clients.client_name")
    site_name: str
    address: Optional[str] = None
    brand_name: Optional[str] = Field(default=None, foreign_key="brands.brand_name")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    id: Optional[int] = Field(default=None, primary_key=True)
    job_number: str = Field(unique=True, index=True)
    date: date
    time: time
    brand: Optional[str] = None
    site_name: Optional[str] = None
    priority: str # Low, Medium, High
    status: str = Field(default="Scheduled") # Scheduled, In Progress, Completed, Cancelled
    client_name: str = Field(foreign_key="clients.client_name")
    company: Optional[str] = None
    address: Optional[str] = None
    engineer_contact_name: str = Field(foreign_key="engineers.contact_name")
    engineer_email: Optional[str] = None
    engineer_phone: Optional[str] = None
    site_contact_name: Optional[str] = Field(default=None, foreign_key="site_contacts.contact_name")
    site_contact_email: Optional[str] = None
    site_contact_phone: Optional[str] = None
    notes: Optional[str] = None
    photos: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EngineerDiary(SQLModel, table=True):
    __tablename__ = "engineer_diary"
    id: Optional[int] = Field(default=None, primary_key=True)
    engineer_name: str = Field(foreign_key="engineers.contact_name")
    date: date
    status: str # enum: Holiday, Sick, Busy, Free
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PasswordReset(SQLModel, table=True):
    __tablename__ = "password_resets"
    id: Optional[int] = Field(default=None, primary_key=True)
    email: Optional[str] = Field(default=None, unique=True)
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
class ExtractionReport(SQLModel, table=True):
    __tablename__ = "extraction_reports"
    id: Optional[int] = Field(default=None, primary_key=True)
    job_number: str = Field(index=True)
    company: str
    date: date
    time: time
    brand: Optional[str] = None
    address: str
    contact_name: str
    contact_number: str
    status: str = Field(default="Draft") # enum: Draft, Submitted, Approved
    risk_pre: Optional[int] = None # 1-6
    risk_post: Optional[int] = None # 1-6
    remedial_requirements: Optional[str] = None
    risk_improvements: Optional[str] = None
    cleaning_interval_current: Optional[str] = None
    cleaning_interval_recommended: Optional[str] = None
    sketch_details: Optional[str] = None
    photos_taken: Optional[str] = None
    photos_path: Optional[str] = None
    client_signature: Optional[str] = None
    engineer_signature: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExtractionMicronReading(SQLModel, table=True):
    __tablename__ = "extraction_micron_readings"
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="extraction_reports.id")
    location: str # T1, T2, etc.
    description: Optional[str] = None # e.g. "Canopy", "Main Duct"
    pre_clean: Optional[int] = None
    post_clean: Optional[int] = None

class ExtractionPhoto(SQLModel, table=True):
    __tablename__ = "extraction_photos"
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="extraction_reports.id")
    photo_type: str # Before, After
    photo_path: str
    caption: Optional[str] = None
    inspection_item: Optional[str] = None # Link to item name if specific

class ExtractionInspectionItem(SQLModel, table=True):
    __tablename__ = "extraction_inspection_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="extraction_reports.id")
    item_name: str
    pre_clean: Optional[str] = None
    success: bool = Field(default=False)
    pass_status: bool = Field(default=False)
    fail_status: bool = Field(default=False)
    advice: Optional[str] = None
    initial: Optional[str] = None

class ExtractionFilterItem(SQLModel, table=True):
    __tablename__ = "extraction_filter_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="extraction_reports.id")
    filter_type: str
    height: Optional[int] = None
    width: Optional[int] = None
    depth: Optional[int] = None
    quantity: Optional[int] = None
    pass_status: bool = Field(default=False)
    fail_status: bool = Field(default=False)
