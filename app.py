import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Import custom components and services
from db.database import DatabaseManager
from components.county_selector import render_county_selector
from components.industry_table import render_industry_table
from components.signals_dashboard import render_signals_dashboard
from components.firm_age_chart import render_firm_age_chart
from components.methodology import render_methodology
from services.data_service import DataService
from services.calculation_service import CalculationService

# Page configuration
st.set_page_config(
    page_title="Financial Advisor Demand Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def init_services():
    """Initialize database and services"""
    db_manager = DatabaseManager()
    data_service = DataService(db_manager)
    calc_service = CalculationService()
    return db_manager, data_service, calc_service

def main():
    """Main application"""
    # Initialize services
    db_manager, data_service, calc_service = init_services()
    
    # Header
    st.title("📊 Financial Advisor Demand Analyzer")
    st.markdown("*Comprehensive county-level market analysis for financial advisory services*")
    
    # Sidebar for county selection and methodology
    with st.sidebar:
        st.header("🎯 County Selection")
        selected_county = render_county_selector()
        
        st.divider()
        
        # Data freshness indicator
        st.header("📅 Data Freshness")
        freshness_data = data_service.get_data_freshness()
        for source, date in freshness_data.items():
            if date:
                color = "🟢" if (datetime.now() - datetime.fromisoformat(date)).days < 30 else "🟡"
                st.write(f"{color} {source}: {date}")
            else:
                st.write(f"🔴 {source}: No data")
        
        st.divider()
        
        # Methodology link
        if st.button("📖 View Methodology", use_container_width=True):
            st.session_state.show_methodology = True
    
    # Main content area
    if not selected_county:
        st.info("👆 Please select a county from the sidebar to begin analysis")
        return
    
    # Show methodology if requested
    if st.session_state.get('show_methodology', False):
        render_methodology()
        if st.button("← Back to Analysis"):
            st.session_state.show_methodology = False
        return
    
    county_fips = selected_county['fips']
    county_name = selected_county['name']
    
    # Coverage banner
    coverage = data_service.get_coverage_status(county_fips)
    coverage_badges = []
    for source, available in coverage.items():
        color = "🟢" if available else "🔴"
        coverage_badges.append(f"{color} {source}")
    
    st.info(f"**Coverage for {county_name}:** {' | '.join(coverage_badges)}")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Industries", "🎯 Demand Signals", "🏢 Firm Analysis", "💰 Capital Access"])
    
    with tab1:
        st.header("Industry Analysis")
        render_industry_table(data_service, county_fips)
    
    with tab2:
        st.header("Demand Signals")
        render_signals_dashboard(data_service, county_fips)
    
    with tab3:
        st.header("Firm Age & Formation Analysis")
        render_firm_age_chart(data_service, county_fips)
    
    with tab4:
        st.header("Capital Access Metrics")
        # SBA lending analysis
        sba_data = data_service.get_sba_data(county_fips)
        if not sba_data.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "SBA Loans per 1K Firms",
                    f"{sba_data['loans_per_1k_firms'].iloc[-1]:.1f}",
                    help="Observed metric based on SBA 7(a) and 504 programs"
                )
            with col2:
                st.metric(
                    "Avg SBA Loan Amount",
                    f"${sba_data['avg_amount'].iloc[-1]:,.0f}",
                    help="Observed metric from SBA loan data"
                )
            
            # Time series chart
            fig = px.line(sba_data, x='year', y='loans_per_1k_firms',
                         title="SBA Lending Trends")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No SBA lending data available for this county")

if __name__ == "__main__":
    main()
