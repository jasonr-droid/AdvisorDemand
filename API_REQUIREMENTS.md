# API Requirements for Financial Advisor Demand Analyzer

## Government Data Sources & API Keys Required

### 1. Census Bureau County Business Patterns (CBP)
- **API Key**: Optional but recommended for higher rate limits
- **Base URL**: https://api.census.gov/data/
- **Data**: Establishment counts, employment, payroll by county and industry
- **Rate Limit**: 500 requests/day without key, 50,000 with key
- **Sign up**: https://api.census.gov/data/key_signup.html
- **Environment Variable**: `CENSUS_API_KEY`

### 2. Bureau of Labor Statistics (BLS) - QCEW
- **API Key**: Optional, public data available without key
- **Base URL**: https://api.bls.gov/publicAPI/v2/
- **Data**: Quarterly employment and wage data
- **Rate Limit**: 25 requests/day without key, 500 with key
- **Sign up**: https://data.bls.gov/registrationEngine/
- **Environment Variable**: `BLS_API_KEY`

### 3. SAM.gov (Federal Contracting Opportunities)
- **API Key**: Required for accessing contracting data
- **Base URL**: https://api.sam.gov/
- **Data**: Federal RFPs, contract awards, entity registrations
- **Rate Limit**: Varies by endpoint
- **Sign up**: https://sam.gov/content/api
- **Environment Variable**: `SAM_API_KEY`

### 4. Small Business Administration (SBA)
- **API Key**: Not required for public loan data
- **Base URL**: https://www.sba.gov/partners/lenders/7a-loan-guarantees
- **Data**: 7(a) and 504 loan program data
- **Format**: Downloadable CSV files, updated quarterly
- **Environment Variable**: None required

### 5. USAspending.gov
- **API Key**: Not required
- **Base URL**: https://api.usaspending.gov/api/v2/
- **Data**: Federal spending and awards by location
- **Rate Limit**: 1000 requests/hour
- **Environment Variable**: None required

### 6. Bureau of Formation Statistics (BFS) - Census
- **API Key**: Same as Census Bureau key
- **Base URL**: https://api.census.gov/data/
- **Data**: Business applications and formations
- **Rate Limit**: Same as Census Bureau
- **Environment Variable**: `CENSUS_API_KEY`

### 7. OpenCorporates (Optional Enhancement)
- **API Key**: Required for API access
- **Base URL**: https://api.opencorporates.com/v0.4/
- **Data**: Corporate registrations and firm demographics
- **Rate Limit**: 200 requests/month free, paid plans available
- **Sign up**: https://opencorporates.com/api_accounts/new
- **Environment Variable**: `OPENCORPORATES_API_KEY`

## Current Application Status

### Working Without API Keys:
- County selection and interface
- Database schema and structure
- Error handling and user feedback
- Data visualization components

### Limited Functionality Without Keys:
- **Industries Tab**: Shows "No industry data available"
- **Demand Signals Tab**: Shows "No RFP/awards data available"  
- **Firm Analysis Tab**: Shows "No firm demographics data available"
- **Capital Access Tab**: Shows "No SBA lending data available"

### Recommended Setup Priority:
1. **CENSUS_API_KEY** - Enables CBP industry data and BFS formation data
2. **SAM_API_KEY** - Enables federal contracting opportunities
3. **BLS_API_KEY** - Enhances employment data quality
4. **OPENCORPORATES_API_KEY** - Optional for enhanced firm demographics

## How to Add API Keys:

The application will prompt you to add these keys when needed. They are stored securely as environment variables and never displayed in the interface.

## Data Privacy & Compliance:

All API calls include:
- Rate limiting to respect service limits
- Automatic retries with exponential backoff
- Source attribution and licensing information
- Small cell suppression for privacy (k<3 rule)
- Clear labeling of "Observed" vs "Estimated" data