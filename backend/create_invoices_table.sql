-- Create invoices table
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    sage_invoice_id VARCHAR(255) UNIQUE,
    invoice_number VARCHAR(100),
    amount DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    sage_synced_at TIMESTAMP,
    error_message TEXT
);

-- Update jobs table
ALTER TABLE jobs ADD COLUMN invoice_raised BOOLEAN DEFAULT FALSE;
ALTER TABLE jobs ADD COLUMN invoice_id INTEGER REFERENCES invoices(id);
