import streamlit as st
import pandas as pd
from datetime import datetime
from lib.utils import DataUtils

def render_methodology():
    """Render methodology documentation page"""
    st.title("📖 Methodology & Data Sources")
    
    st.markdown("""
    This page provides comprehensive documentation of the data sources, methodologies, 
    and calculations used in the Financial Advisor Demand Analyzer.
    """)
    
    # Data Sources Section
    st.header("🗃️ Data Sources")
    
    data_sources = [
        {
            "source": "Census Bureau County Business Patterns (CBP)",
            "type": "Observed",
            "description": "Establishment counts, employment, and annual payroll by county and NAICS code",
            "frequency": "Annual",
            "license": "Public Domain",
            "url": "https://www.census.gov/programs-surveys/cbp.html"
        },
        {
            "source": "Bureau of Labor Statistics QCEW",
            "type": "Observed", 
            "description": "Quarterly employment and average weekly wages by county and industry",
            "frequency": "Quarterly",
            "license": "Public Domain",
            "url": "https://www.bls.gov/cew/"
        },
        {
            "source": "SBA Loan Programs (7a/504)",
            "type": "Observed",
            "description": "Small Business Administration loan approvals, amounts, and recipient data",
            "frequency": "Updated regularly",
            "license": "Public Domain", 
            "url": "https://www.sba.gov/about-sba/open-government/foia/frequently-requested-records"
        },
        {
            "source": "SAM.gov Opportunities",
            "type": "Observed",
            "description": "Federal contracting opportunities and RFPs",
            "frequency": "Real-time",
            "license": "Public Domain",
            "url": "https://sam.gov/data-services"
        },
        {
            "source": "USAspending.gov Awards",
            "type": "Observed",
            "description": "Federal contract awards and spending data",
            "frequency": "Daily updates",
            "license": "Public Domain",
            "url": "https://www.usaspending.gov/download_center/api_guide"
        },
        {
            "source": "City Business Licenses",
            "type": "Observed",
            "description": "Business license issuances from major cities (LA, San Diego, San Francisco)",
            "frequency": "Varies by city",
            "license": "Open Data",
            "url": "Various city open data portals"
        },
        {
            "source": "OpenCorporates",
            "type": "Observed",
            "description": "Corporate registration and incorporation date data",
            "frequency": "Updated regularly",
            "license": "OpenCorporates License",
            "url": "https://opencorporates.com/"
        },
        {
            "source": "Bureau of Formation Statistics (BFS)",
            "type": "Observed",
            "description": "County-level business formation applications",
            "frequency": "Annual",
            "license": "Public Domain",
            "url": "https://www.census.gov/econ/bfs/"
        }
    ]
    
    # Create data sources table
    sources_df = pd.DataFrame(data_sources)
    
    for _, source in sources_df.iterrows():
        with st.expander(f"{source['source']} - {DataUtils.get_data_badge(source['type'])}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Description:** {source['description']}")
                st.markdown(f"**Update Frequency:** {source['frequency']}")
            
            with col2:
                st.markdown(f"**License:** {source['license']}")
                st.markdown(f"**URL:** [{source['source']}]({source['url']})")
    
    # Data Labels Section
    st.header("🏷️ Data Quality Labels")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        ### {DataUtils.get_data_badge('Observed')} Observed
        Data directly measured or reported by authoritative sources:
        - CBP establishment and employment counts
        - QCEW employment and wage data
        - SBA loan records
        - Federal RFP postings and awards
        - Business license issuances
        - Corporate incorporation dates
        """)
    
    with col2:
        st.markdown(f"""
        ### {DataUtils.get_data_badge('Proxy')} Proxy
        Indicators that suggest market demand but require interpretation:
        - Service categories extracted from RFP text
        - Industry classifications from license data
        - Geographic matching of opportunities
        """)
    
    with col3:
        st.markdown(f"""
        ### {DataUtils.get_data_badge('Estimated')} Estimated
        Calculated metrics derived from observed data:
        - Revenue estimates (when available)
        - Market size projections
        - Derived ratios and indices
        """)
    
    # Calculations Section
    st.header("🧮 Key Calculations")
    
    calculations = [
        {
            "metric": "SBA Loans per 1K Firms",
            "formula": "(Number of SBA Loans / CBP Establishments) × 1,000",
            "description": "Standardized measure of capital access relative to firm population",
            "data_type": "Observed"
        },
        {
            "metric": "SBA Amount per 1K Firms", 
            "formula": "(Total SBA Loan Amount / CBP Establishments) × 1,000",
            "description": "Dollar amount of SBA lending per thousand firms",
            "data_type": "Observed"
        },
        {
            "metric": "RFPs per 1K Employment",
            "formula": "(Number of RFPs / QCEW Employment) × 1,000", 
            "description": "Federal contracting opportunities relative to employment base",
            "data_type": "Observed"
        },
        {
            "metric": "Firm Age Distribution",
            "formula": "Age = Current Year - Incorporation Year",
            "description": "Categorized into buckets: 0-1, 1-3, 3-5, 5+ years",
            "data_type": "Observed"
        },
        {
            "metric": "High Propensity Rate",
            "formula": "(High Propensity Applications / Total Applications) × 100",
            "description": "Percentage of business applications with high likelihood of becoming operational",
            "data_type": "Observed"
        },
        {
            "metric": "Capital Access Index",
            "formula": "Weighted combination of SBA metrics, min-max normalized 0-100",
            "description": "Composite score of capital availability (default weights: amount=0.6, count=0.4)",
            "data_type": "Estimated"
        }
    ]
    
    for calc in calculations:
        with st.expander(f"{calc['metric']} - {DataUtils.get_data_badge(calc['data_type'])}"):
            st.markdown(f"**Formula:** `{calc['formula']}`")
            st.markdown(f"**Description:** {calc['description']}")
    
    # Privacy and Compliance Section
    st.header("🔒 Privacy & Compliance")
    
    st.markdown("""
    ### Small Cell Suppression
    - Any metric representing fewer than 3 entities is suppressed and displayed as "—"
    - This follows standard statistical disclosure control practices
    - Protects individual business privacy while maintaining analytical utility
    
    ### Data Retention
    - No personally identifiable information (PII) is stored
    - Email addresses and phone numbers are stripped from RFP text if present
    - Only aggregated, statistical data is retained
    
    ### Terms of Service Compliance
    - All data sources are accessed through official APIs or public datasets
    - No web scraping that violates terms of service
    - Rate limiting implemented to respect API guidelines
    """)
    
    # Data Freshness Section
    st.header("📅 Data Freshness & Updates")
    
    update_schedule = [
        {"Source": "CBP", "Frequency": "Annual", "Typical Lag": "12-18 months"},
        {"Source": "QCEW", "Frequency": "Quarterly", "Typical Lag": "5-6 months"},
        {"Source": "SBA Loans", "Frequency": "Monthly", "Typical Lag": "1-2 months"},
        {"Source": "SAM.gov RFPs", "Frequency": "Daily", "Typical Lag": "Real-time"},
        {"Source": "USAspending", "Frequency": "Daily", "Typical Lag": "1-30 days"},
        {"Source": "Business Licenses", "Frequency": "Varies", "Typical Lag": "1-30 days"},
        {"Source": "OpenCorporates", "Frequency": "Ongoing", "Typical Lag": "Varies"},
        {"Source": "BFS", "Frequency": "Annual", "Typical Lag": "12-18 months"}
    ]
    
    update_df = pd.DataFrame(update_schedule)
    st.dataframe(update_df, use_container_width=True, hide_index=True)
    
    # Limitations Section
    st.header("⚠️ Known Limitations")
    
    st.warning("""
    **Geographic Coverage:**
    - Business license data limited to select major cities
    - OpenCorporates coverage varies by state
    - Some rural counties may have limited data availability
    
    **Industry Coverage:**
    - Focus on financial services and related NAICS codes
    - May not capture all relevant business activities
    - Industry classifications can be inconsistent across sources
    
    **Temporal Coverage:**
    - Historical data availability varies by source
    - Some datasets have significant reporting lags
    - Trend analysis limited by data vintage
    
    **Data Quality:**
    - Government datasets may contain errors or omissions
    - NAICS code assignments can be inaccurate
    - Geographic matching is approximate in some cases
    """)
    
    # Contact and Updates Section
    st.header("📞 Contact & Updates")
    
    st.info("""
    **Methodology Updates:**
    This methodology documentation is version-controlled and updated when:
    - New data sources are added
    - Calculation methods change
    - Data quality improvements are implemented
    
    **Data Issues:**
    If you notice data quality issues or have questions about specific metrics,
    please review the source documentation linked above or check the data
    freshness indicators in the main application.
    """)
    
    # Export methodology as JSON
    st.header("📥 Export Methodology")
    
    if st.button("Generate Methodology JSON"):
        methodology_json = generate_methodology_json()
        
        st.download_button(
            label="Download Methodology JSON",
            data=methodology_json,
            file_name=f"methodology_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

def generate_methodology_json():
    """Generate methodology as JSON for API endpoint"""
    methodology = {
        "version": "1.0",
        "last_updated": datetime.now().isoformat(),
        "data_sources": {
            "cbp": {
                "name": "Census Bureau County Business Patterns",
                "type": "Observed",
                "url": "https://www.census.gov/programs-surveys/cbp.html",
                "license": "Public Domain",
                "frequency": "Annual",
                "typical_lag_months": 15
            },
            "qcew": {
                "name": "Bureau of Labor Statistics QCEW",
                "type": "Observed", 
                "url": "https://www.bls.gov/cew/",
                "license": "Public Domain",
                "frequency": "Quarterly",
                "typical_lag_months": 6
            },
            "sba": {
                "name": "SBA Loan Programs",
                "type": "Observed",
                "url": "https://www.sba.gov/about-sba/open-government/foia/frequently-requested-records",
                "license": "Public Domain",
                "frequency": "Monthly",
                "typical_lag_months": 2
            },
            "sam": {
                "name": "SAM.gov Opportunities",
                "type": "Observed",
                "url": "https://sam.gov/data-services",
                "license": "Public Domain", 
                "frequency": "Real-time",
                "typical_lag_months": 0
            },
            "usaspending": {
                "name": "USAspending.gov Awards",
                "type": "Observed",
                "url": "https://www.usaspending.gov/download_center/api_guide",
                "license": "Public Domain",
                "frequency": "Daily",
                "typical_lag_days": 15
            },
            "licenses": {
                "name": "City Business Licenses",
                "type": "Observed",
                "url": "Various city open data portals",
                "license": "Open Data",
                "frequency": "Varies",
                "coverage": ["Los Angeles", "San Diego", "San Francisco"]
            },
            "opencorporates": {
                "name": "OpenCorporates",
                "type": "Observed",
                "url": "https://opencorporates.com/",
                "license": "OpenCorporates License",
                "frequency": "Ongoing",
                "coverage": "Varies by jurisdiction"
            },
            "bfs": {
                "name": "Bureau of Formation Statistics",
                "type": "Observed",
                "url": "https://www.census.gov/econ/bfs/",
                "license": "Public Domain",
                "frequency": "Annual",
                "typical_lag_months": 15
            }
        },
        "calculations": {
            "sba_loans_per_1k_firms": {
                "formula": "(Number of SBA Loans / CBP Establishments) × 1,000",
                "data_type": "Observed",
                "denominator_source": "CBP"
            },
            "sba_amount_per_1k_firms": {
                "formula": "(Total SBA Loan Amount / CBP Establishments) × 1,000",
                "data_type": "Observed", 
                "denominator_source": "CBP"
            },
            "rfps_per_1k_employment": {
                "formula": "(Number of RFPs / QCEW Employment) × 1,000",
                "data_type": "Observed",
                "denominator_source": "QCEW"
            },
            "capital_access_index": {
                "formula": "Weighted combination of SBA metrics, min-max normalized 0-100",
                "data_type": "Estimated",
                "weights": {"amount_per_1k": 0.6, "count_per_1k": 0.4}
            }
        },
        "data_quality": {
            "suppression_threshold": 3,
            "suppression_rule": "Any metric representing fewer than 3 entities is suppressed",
            "pii_policy": "No personally identifiable information is stored",
            "terms_compliance": "All data accessed through official APIs only"
        },
        "known_limitations": {
            "geographic_coverage": "Business license data limited to select cities",
            "industry_coverage": "Focus on financial services NAICS codes",
            "temporal_coverage": "Historical availability varies by source",
            "data_quality": "Government datasets may contain errors or omissions"
        }
    }
    
    import json
    return json.dumps(methodology, indent=2)
