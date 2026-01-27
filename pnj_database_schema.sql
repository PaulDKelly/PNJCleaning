USE bkxatnkyyu;

-- Drop tables in reverse order
DROP TABLE IF EXISTS password_resets;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS engineer_diary;
DROP TABLE IF EXISTS job_schedule;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS site_contacts;
DROP TABLE IF EXISTS engineers;
DROP TABLE IF EXISTS clients;

-- Create tables
CREATE TABLE clients (
  client_name VARCHAR(255) PRIMARY KEY COLLATE utf8mb4_unicode_ci,
  company VARCHAR(255),
  address TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE engineers (
  contact_name VARCHAR(255) PRIMARY KEY COLLATE utf8mb4_unicode_ci,
  email VARCHAR(255),
  phone VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE site_contacts (
  contact_name VARCHAR(255) PRIMARY KEY COLLATE utf8mb4_unicode_ci,
  email VARCHAR(255),
  phone VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE jobs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  submission_id VARCHAR(255),
  job_number VARCHAR(255) NOT NULL,
  date DATE NOT NULL,
  time TIME NOT NULL,
  priority ENUM('Low', 'Medium', 'High') NOT NULL,
  client_name VARCHAR(255) NOT NULL COLLATE utf8mb4_unicode_ci,
  company VARCHAR(255),
  address TEXT,
  engineer_contact_name VARCHAR(255) NOT NULL COLLATE utf8mb4_unicode_ci,
  engineer_email VARCHAR(255),
  engineer_phone VARCHAR(255),
  site_contact_name VARCHAR(255) COLLATE utf8mb4_unicode_ci,
  site_contact_email VARCHAR(255),
  site_contact_phone VARCHAR(255),
  notes TEXT,
  photos TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (client_name) REFERENCES clients(client_name) ON DELETE RESTRICT,
  FOREIGN KEY (engineer_contact_name) REFERENCES engineers(contact_name) ON DELETE RESTRICT,
  FOREIGN KEY (site_contact_name) REFERENCES site_contacts(contact_name) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Remaining tables (unchanged)
CREATE TABLE job_schedule (
  id INT AUTO_INCREMENT PRIMARY KEY,
  job_number VARCHAR(255) NOT NULL,
  client_name VARCHAR(255) NOT NULL COLLATE utf8mb4_unicode_ci,
  brand VARCHAR(255),
  date DATE NOT NULL,
  time TIME NOT NULL,
  status ENUM('Scheduled', 'In Progress', 'Completed', 'Cancelled') NOT NULL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (client_name) REFERENCES clients(client_name) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE engineer_diary (
  id INT AUTO_INCREMENT PRIMARY KEY,
  engineer_name VARCHAR(255) NOT NULL COLLATE utf8mb4_unicode_ci,
  date DATE NOT NULL,
  status ENUM('Holiday', 'Sick', 'Busy', 'Free') NOT NULL,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (engineer_name) REFERENCES engineers(contact_name) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE password_resets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  token VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;