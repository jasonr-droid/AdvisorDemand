-- Financial Advisor Demand Analyzer Database Schema
-- SQLite database for caching normalized government data

-- Industry data from Census Bureau County Business Patterns
CREATE TABLE IF NOT EXISTS industry_cbp (
    county_fips TEXT NOT NULL,
    naics TEXT NOT NULL,
    year INTEGER NOT NULL,
    establishments INTEGER,
    employment INTEGER,
    annual_payroll REAL,
    suppressed INTEGER DEFAULT 0,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL,
    PRIMARY KEY (county_fips, naics, year)
);

-- Employment and wage data from Bureau of Labor Statistics QCEW
CREATE TABLE IF NOT EXISTS industry_qcew (
    county_fips TEXT NOT NULL,
    naics TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    employment INTEGER,
    avg_weekly_wage REAL,
    suppressed INTEGER DEFAULT 0,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL,
    PRIMARY KEY (county_fips, naics, year, quarter)
);

-- SBA lending data
CREATE TABLE IF NOT EXISTS sba_loans (
    loan_id TEXT PRIMARY KEY,
    county_fips TEXT NOT NULL,
    fy INTEGER NOT NULL,
    program TEXT NOT NULL,
    amount REAL NOT NULL,
    lender TEXT,
    naics TEXT,
    approval_date TEXT,
    borrower_name TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Federal RFP opportunities from SAM.gov
CREATE TABLE IF NOT EXISTS rfp_opps (
    notice_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    naics TEXT,
    place_county_fips TEXT,
    posted_date TEXT NOT NULL,
    close_date TEXT,
    url TEXT,
    agency TEXT,
    office TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Federal contract awards from USAspending
CREATE TABLE IF NOT EXISTS awards (
    award_id TEXT PRIMARY KEY,
    naics TEXT,
    recipient_county_fips TEXT NOT NULL,
    amount REAL NOT NULL,
    action_date TEXT NOT NULL,
    agency TEXT,
    recipient_name TEXT,
    award_type TEXT,
    url TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Business licenses from local jurisdictions
CREATE TABLE IF NOT EXISTS business_licenses (
    license_id TEXT PRIMARY KEY,
    jurisdiction TEXT NOT NULL,
    county_fips TEXT NOT NULL,
    business_name TEXT,
    naics TEXT,
    license_type TEXT,
    issued_date TEXT NOT NULL,
    expiry_date TEXT,
    status TEXT,
    geocode TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Firm incorporation data from OpenCorporates
CREATE TABLE IF NOT EXISTS firms (
    company_id TEXT PRIMARY KEY,
    jurisdiction TEXT NOT NULL,
    company_number TEXT NOT NULL,
    company_name TEXT,
    county_fips TEXT,
    incorporation_date TEXT,
    company_type TEXT,
    status TEXT,
    registered_address TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Business formation statistics from Bureau of Formation Statistics
CREATE TABLE IF NOT EXISTS bfs_county (
    county_fips TEXT NOT NULL,
    year INTEGER NOT NULL,
    applications_total INTEGER NOT NULL,
    high_propensity_apps INTEGER,
    applications_with_planned_wages INTEGER,
    applications_with_first_day_wages INTEGER,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL,
    PRIMARY KEY (county_fips, year)
);

-- NAICS code mappings and descriptions
CREATE TABLE IF NOT EXISTS naics_codes (
    naics TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    level INTEGER NOT NULL
);

-- County FIPS code mappings
CREATE TABLE IF NOT EXISTS counties (
    fips TEXT PRIMARY KEY,
    state_code TEXT NOT NULL,
    county_name TEXT NOT NULL,
    state_name TEXT NOT NULL,
    combined_name TEXT NOT NULL
);

-- Data refresh tracking
CREATE TABLE IF NOT EXISTS data_refresh_log (
    source TEXT NOT NULL,
    county_fips TEXT,
    last_refresh TEXT NOT NULL,
    status TEXT NOT NULL,
    records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    PRIMARY KEY (source, county_fips)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cbp_county_naics ON industry_cbp(county_fips, naics);
CREATE INDEX IF NOT EXISTS idx_qcew_county_naics ON industry_qcew(county_fips, naics);
CREATE INDEX IF NOT EXISTS idx_sba_county ON sba_loans(county_fips);
CREATE INDEX IF NOT EXISTS idx_rfp_county ON rfp_opps(place_county_fips);
CREATE INDEX IF NOT EXISTS idx_awards_county ON awards(recipient_county_fips);
CREATE INDEX IF NOT EXISTS idx_licenses_county ON business_licenses(county_fips);
CREATE INDEX IF NOT EXISTS idx_firms_county ON firms(county_fips);
CREATE INDEX IF NOT EXISTS idx_bfs_county ON bfs_county(county_fips);

-- Insert default NAICS codes for financial services
INSERT OR IGNORE INTO naics_codes (naics, title, level) VALUES 
('52', 'Finance and Insurance', 2),
('523', 'Securities, Commodity Contracts, and Other Financial Investments and Related Activities', 3),
('5239', 'Other Financial Investment Activities', 4),
('52393', 'Investment Advice', 5),
('523930', 'Investment Advice', 6),
('541', 'Professional, Scientific, and Technical Services', 3),
('5412', 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services', 4),
('54121', 'Accounting, Tax Preparation, Bookkeeping, and Payroll Services', 5),
('541211', 'Offices of Certified Public Accountants', 6),
('541213', 'Tax Preparation Services', 6),
('541214', 'Payroll Services', 6);

-- Insert sample counties for testing
INSERT OR IGNORE INTO counties (fips, state_code, county_name, state_name, combined_name) VALUES 
('06037', 'CA', 'Los Angeles County', 'California', 'Los Angeles County, CA'),
('06073', 'CA', 'San Diego County', 'California', 'San Diego County, CA'),
('06075', 'CA', 'San Francisco County', 'California', 'San Francisco County, CA'),
('36061', 'NY', 'New York County', 'New York', 'New York County, NY'),
('17031', 'IL', 'Cook County', 'Illinois', 'Cook County, IL'),
('48201', 'TX', 'Harris County', 'Texas', 'Harris County, TX'),
('04013', 'AZ', 'Maricopa County', 'Arizona', 'Maricopa County, AZ'),
('12086', 'FL', 'Miami-Dade County', 'Florida', 'Miami-Dade County, FL'),
('53033', 'WA', 'King County', 'Washington', 'King County, WA'),
('25025', 'MA', 'Suffolk County', 'Massachusetts', 'Suffolk County, MA');
