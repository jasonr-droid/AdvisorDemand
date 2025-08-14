-- County Business Patterns data
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

-- QCEW data
CREATE TABLE IF NOT EXISTS industry_qcew (
    county_fips TEXT NOT NULL,
    naics TEXT NOT NULL,
    year INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    employment INTEGER,
    avg_weekly_wage REAL,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL,
    PRIMARY KEY (county_fips, naics, year, quarter)
);

-- SBA loans
CREATE TABLE IF NOT EXISTS sba_loans (
    loan_id TEXT PRIMARY KEY,
    county_fips TEXT NOT NULL,
    fy INTEGER NOT NULL,
    program TEXT NOT NULL,
    amount REAL NOT NULL,
    lender TEXT,
    naics TEXT,
    approval_date TEXT NOT NULL,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Federal RFPs and opportunities
CREATE TABLE IF NOT EXISTS rfp_opps (
    notice_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    naics TEXT,
    place_county_fips TEXT,
    posted_date TEXT NOT NULL,
    close_date TEXT,
    url TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Federal awards
CREATE TABLE IF NOT EXISTS awards (
    award_id TEXT PRIMARY KEY,
    naics TEXT,
    recipient_county_fips TEXT NOT NULL,
    amount REAL NOT NULL,
    action_date TEXT NOT NULL,
    agency TEXT,
    url TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Business licenses
CREATE TABLE IF NOT EXISTS business_licenses (
    license_id TEXT PRIMARY KEY,
    jurisdiction TEXT NOT NULL,
    county_fips TEXT NOT NULL,
    naics TEXT,
    issued_date TEXT NOT NULL,
    status TEXT,
    geocode TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Firm data from OpenCorporates
CREATE TABLE IF NOT EXISTS firms (
    company_id TEXT PRIMARY KEY,
    jurisdiction TEXT NOT NULL,
    company_number TEXT NOT NULL,
    county_fips TEXT,
    incorporation_date TEXT,
    status TEXT,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL
);

-- Business formation statistics
CREATE TABLE IF NOT EXISTS bfs_county (
    county_fips TEXT NOT NULL,
    year INTEGER NOT NULL,
    applications_total INTEGER NOT NULL,
    high_propensity_apps INTEGER,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    license TEXT NOT NULL,
    PRIMARY KEY (county_fips, year)
);

-- Data freshness tracking
CREATE TABLE IF NOT EXISTS data_freshness (
    source_name TEXT PRIMARY KEY,
    last_updated TEXT NOT NULL,
    status TEXT NOT NULL,
    records_count INTEGER DEFAULT 0
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
