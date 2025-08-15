# Financial Advisor Demand Analyzer

## Overview

The Financial Advisor Demand Analyzer is a comprehensive web application that analyzes county-level market opportunities for financial advisory services. The system aggregates data from multiple government sources to provide insights into industry size, demand signals, firm demographics, and market dynamics for financial advisors looking to establish or expand their practice in specific U.S. counties.

The application provides both observed data (directly from government sources) and calculated metrics (derived from multiple data points) to help financial advisors make informed decisions about market entry and business development strategies.

## Recent Changes (August 2025)

### Data Integration Success
- **Census Bureau API Integration**: Successfully connected to live Census Bureau County Business Patterns API with real API credentials
- **Authentic Data Pipeline**: Industries tab now displays real government data (53,591 establishments, 917,211 employees, $48.8B payroll for Clark County, NV)
- **Data Quality Assessment**: Implemented working data quality scoring with Grade A ratings for government data

### Technical Fixes Completed
- **Database Connection**: Fixed DataService to properly return DataFrames instead of query lists
- **Data Type Handling**: Resolved AttributeError crashes related to data type conversions
- **Table Formatting**: Fixed column mapping issues to display available data fields properly
- **Chart Compatibility**: Updated all Plotly charts to use available columns (NAICS codes) instead of missing industry titles
- **Quality Filtering**: Implemented small cell suppression and privacy compliance features
- **Financial Services Filter**: Fixed "Show only financial services" checkbox crash by adding dynamic NAICS classification

### Data Persistence Implementation (August 14, 2025)
- **Cache Manager**: Implemented comprehensive caching system to retain API data during troubleshooting
- **Smart Caching**: 24-48 hour retention periods based on data source update frequency (CBP: 24h, SBA: 48h, etc.)
- **Development Mode**: Cache prevents repeated API calls while fixing display issues
- **County Expansion**: Added Santa Barbara County and other major CA counties to searchable list
- **Cache UI**: Added cache management interface in sidebar for development transparency

### Security and UX Enhancements (August 14, 2025)
- **SQL Security**: Fixed dynamic SQL construction patterns with hardcoded table configurations to prevent injection vulnerabilities
- **Demand Signals Fix**: Resolved signal type mapping issues causing empty tabs in demand signals dashboard
- **Data Source Transparency**: Enhanced license tab with county-specific data availability information and authentic source links
- **Error Handling**: Improved empty state messaging with actionable guidance for alternative data collection methods
- **Business License Data**: Confirmed Santa Barbara County lacks public API access for business license data; dashboard correctly displays "Limited" coverage status with manual data collection guidance

### Advanced Analytics Integration (August 14, 2025)
- **Demand Scoring Service**: Implemented sophisticated multi-signal demand scoring using weighted z-score normalization
- **Industry Prioritization**: Added NAICS-level demand analysis combining BFS applications, license activity, and RFP opportunities
- **Market Sizing**: Integrated spend estimation algorithms based on establishment size proxies and industry benchmarks
- **Target Company Identification**: Created heuristic-based company targeting using recent licensing and formation activity
- **Enhanced SQL Analytics**: Incorporated user-requested establishment counting queries with proper year filtering and aggregation
- **Dashboard Facade Pattern**: Added get_demand_dashboard() method for efficient data loading across scoring components
- **Performance Optimization**: Implemented one-stop data payload system with refresh_all_data() capability for development use

### UI/UX Improvements (August 14, 2025)
- **Dark Mode Implementation**: Successfully implemented dark theme with professional color scheme for improved visibility
- **Industry Name Enhancement**: Replaced all numeric NAICS codes with descriptive industry names across tables and charts
- **Currency Formatting**: Added proper dollar formatting for Annual Payroll columns ($10,891,000 format)
- **Chart Consistency**: Updated all employment, establishment, and payroll charts to use descriptive industry names
- **Financial Services Mapping**: Enhanced NAICS mapper with comprehensive financial services industry codes (Commercial Banking, Insurance Agencies, etc.)

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit-based web application with modular component architecture
- **Component Structure**: Organized into reusable components for county selection, industry analysis, signals dashboard, firm age charts, and methodology documentation
- **Data Visualization**: Plotly integration for interactive charts and graphs
- **State Management**: Streamlit's session state for maintaining user selections and cached data

### Backend Architecture
- **Application Layer**: Python-based application with service-oriented architecture
- **Data Services**: Separated data fetching (DataService) and calculation logic (CalculationService)
- **Adapter Pattern**: Individual adapters for each government data source (CBP, QCEW, SBA, SAM.gov, etc.)
- **Caching Strategy**: Resource caching using Streamlit's `@st.cache_resource` decorator for database connections and services

### Data Storage Solutions
- **Primary Database**: SQLite database managed through DatabaseManager class
- **Schema Management**: SQL schema files for database initialization and structure
- **Data Persistence**: Local file-based storage for cached government data
- **Privacy Compliance**: Built-in small cell suppression (k<3) for privacy protection

### Authentication and Authorization
- **API Keys**: Environment variable-based configuration for optional government API keys
- **Rate Limiting**: Built-in rate limiting for all external API calls
- **Data Licensing**: Automatic license and source URL tracking for all imported data

### Data Quality and Compliance
- **Data Labeling**: Clear distinction between "Observed" (direct government data) and "Estimated/Proxy" (calculated) metrics
- **Data Suppression**: Automatic suppression of small cell counts for privacy compliance
- **Source Attribution**: Every data point includes source URL, retrieval timestamp, and license information
- **Quality Assessment**: DataQualityManager for assessing and reporting data completeness and reliability

## External Dependencies

### Government Data Sources
- **Census Bureau County Business Patterns (CBP)**: Establishment counts, employment, and payroll by county and NAICS code
- **Bureau of Labor Statistics QCEW**: Quarterly employment and wage data by county and industry
- **Small Business Administration (SBA)**: Loan programs data (7a/504) for capital access analysis
- **SAM.gov**: Federal contracting opportunities and RFPs
- **USAspending.gov**: Federal awards and spending data by location
- **Bureau of Formation Statistics (BFS)**: Business formation and application data
- **OpenCorporates**: Corporate registration and firm demographic data
- **City Business License APIs**: Municipal business license data from major cities

### Technical Dependencies
- **Core Framework**: Streamlit for web application framework
- **Data Processing**: Pandas and NumPy for data manipulation and analysis
- **Visualization**: Plotly Express and Plotly Graph Objects for interactive charts
- **Database**: SQLite with better-sqlite3 compatibility for local data storage
- **HTTP Requests**: Requests library for API calls with built-in retry logic
- **Date Handling**: Python datetime and custom date utility classes

### API Integrations
- **Census API**: Optional API key for enhanced data access
- **BLS API**: Optional API key for QCEW data
- **SAM.gov API**: Optional API key for federal opportunities
- **OpenCorporates API**: Optional API key for enhanced firm data
- **City Data Portals**: Socrata/CKAN APIs for municipal data sources

### Data Processing Libraries
- **NAICS Mapping**: Custom library for industry code classification and hierarchy
- **FIPS Utilities**: Custom library for county and state code management
- **Data Quality**: Custom utilities for privacy compliance and data validation
- **Calculation Engine**: Custom service for derived metrics and scoring algorithms