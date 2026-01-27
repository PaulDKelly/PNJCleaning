# PNJ Extraction Management Portal

A high-fidelity compliance and reporting system for PNJ Cleaning, designed to manage deep kitchen extraction cleans, technical TR/19 auditing, and client reporting.

## 🚀 Key Features

- **Personalized Engineer Diary**: Mobile-friendly job queue for field staff with one-click audit starting.
- **Unified Management Dashboard**: Real-time visibility into active jobs, scheduling, and staff allocation.
- **High-Fidelity TR/19 Auditing**: Professional digital forms capturing micron readings, risk assessments, and photographic evidence.
- **Admin Curation Flow**: Full oversight for managers to edit and refine reports before finalization.
- **Professional PDF Engine**: 1:1 design matching of official PNJ certificates and audit documentation.
- **WhatsApp Dispatch**: One-click job details sent directly to staff via WhatsApp.
- **Secure Client Portal**: Token-based access for customers to view compliance history and download certificates.

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTMX, Jinja2, Tailwind CSS, DaisyUI
- **Database**: SQLModel (SQLAlchemy) with SQLite/MySQL compatibility
- **PDF Generation**: fpdf2

## 📦 Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone [repository-url]
   cd PNJCleaning/backend
   ```

2. **Set up Python environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file in the `backend` directory:
   ```env
   DATABASE_URL=sqlite:///./pnj_database.db
   SECRET_KEY=your_secure_secret_key
   ```

4. **Run the Application**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

## 🛡️ Security
This system uses token-based authentication for clients and role-based access for managers and engineers. Ensure the `SECRET_KEY` is not committed to version control in production environments.
